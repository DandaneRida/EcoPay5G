import re
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from app.camara.client import NokiaNaCClient
from app.agent.state import AgentState

nokia_client = NokiaNaCClient()

@tool
def verify_number_tool(phone_number: str) -> str:
    """CAMARA Tool: Validate user network identity."""
    res = nokia_client.verify_number(phone_number)
    mode_str = res.get("mode", "UNKNOWN")
    if res.get("devicePhoneNumberVerified"):
        return f"IDENTITY_VERIFIED: Network identity confirmed. [Mode: {mode_str}]"
    return f"IDENTITY_FAILED: Device mismatch detected. Deposit rejected. [Mode: {mode_str}]"

@tool
def check_sim_swap_tool(phone_number: str) -> str:
    """CAMARA Tool: Verify SIM security status."""
    res = nokia_client.check_sim_swap(phone_number)
    mode_str = res.get("mode", "UNKNOWN")
    if res.get("swapped"):
        return f"FRAUD_ALERT: SIM swap detected within 24h. Deposit rejected. [Mode: {mode_str}]"
    return f"SECURITY_OK: SIM validated. [Mode: {mode_str}]"

@tool
def request_qod_tool(phone_number: str) -> str:
    """CAMARA Tool: Trigger 5G network boost."""
    res = nokia_client.request_qod(phone_number)
    mode_str = res.get("mode", "UNKNOWN")
    status = res.get("qosStatus", "ACTIVE")
    return f"QOD_BOOST_GRANTED: 5G priority active (Status: {status}). [Mode: {mode_str}]"

tools = [verify_number_tool, check_sim_swap_tool, request_qod_tool]

def parse_deposit_info(messages):
    full_text = " ".join([str(getattr(m, 'content', '')) for m in messages])
    phone_match = re.search(r"\+?\d{10,15}", full_text)
    phone = phone_match.group(0) if phone_match else "+358400000001"

    waste_match = re.search(r"Waste=([a-zA-Z]+)", full_text, re.IGNORECASE)
    if waste_match:
        waste = waste_match.group(1).lower()
    else:
        material_search = re.search(r"\b(plastic|glass|metal)\b", full_text, re.IGNORECASE)
        waste = material_search.group(1).lower() if material_search else "plastic"

    weight_match = re.search(r"Weight=(\d+)", full_text, re.IGNORECASE)
    if not weight_match:
        weight_match = re.search(r"(\d+)\s*g", full_text, re.IGNORECASE)
    weight = int(weight_match.group(1)) if weight_match else 0
    return phone, waste, weight

def calculate_tokens(waste: str, weight: int) -> float:
    rates = {"plastic": 0.1, "glass": 0.05, "metal": 0.15}
    return round(weight * rates.get(waste.lower(), 0.1), 2)

def call_model(state: AgentState):
    """Executes the sequential CAMARA logic flow."""
    messages = list(state.get("messages", []))
    phone = state.get("phone")
    waste = state.get("waste")
    weight = state.get("weight")

    if not phone or not waste or weight is None or weight == 0:
        p, wa, we = parse_deposit_info(messages)
        phone, waste, weight = phone or p, waste or wa, weight or we

    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    has_nv = any("IDENTITY" in str(m.content) for m in tool_messages)
    has_sim = any("SECURITY" in str(m.content) or "FRAUD" in str(m.content) for m in tool_messages)
    has_qod = any("QOD_BOOST" in str(m.content) for m in tool_messages)

    # Step 1: Number Verification
    if not has_nv:
        return {
            "phone": phone, "waste": waste, "weight": weight,
            "messages": [AIMessage(content="", tool_calls=[{"name": "verify_number_tool", "args": {"phone_number": phone}, "id": "nv_check"}])]
        }

    nv_output = next((m.content for m in tool_messages if "IDENTITY" in str(m.content)), "")
    identity_failed = "IDENTITY_FAILED" in str(nv_output)

    # Step 2: SIM Swap Check
    if not identity_failed and not has_sim:
        return {
            "phone": phone, "waste": waste, "weight": weight,
            "messages": [AIMessage(content="", tool_calls=[{"name": "check_sim_swap_tool", "args": {"phone_number": phone}, "id": "sim_check"}])]
        }

    sim_output = next((m.content for m in tool_messages if "SECURITY" in str(m.content) or "FRAUD" in str(m.content)), "")
    is_fraud = "FRAUD_ALERT" in str(sim_output)

    # Step 3: QoD Request
    if not identity_failed and not is_fraud and weight > 1000 and not has_qod:
        return {
            "phone": phone, "waste": waste, "weight": weight,
            "messages": [AIMessage(content="", tool_calls=[{"name": "request_qod_tool", "args": {"phone_number": phone}, "id": "qod_boost"}])]
        }

    # Step 4: Output Synthesis
    status = "REJECTED" if identity_failed or is_fraud else "APPROVED"
    tokens = 0.0 if status == "REJECTED" else calculate_tokens(waste, weight)
    qod_status = "Not Evaluated"
    if status == "APPROVED":
        qod_status = "Active" if weight > 1000 else "Not Required"

    report_text = f"""### Deposit Decision Report
- **Number Verification:** {nv_output.split('[')[0].strip() if nv_output else 'Failed / Skipped'}
- **Security Check:** {sim_output.split('[')[0].strip() if sim_output else 'Failed / Skipped'}
- **5G Network Boost:** {qod_status}
- **Recycled Material:** {waste.upper()} ({weight}g)
- **EcoTokens Awarded:** {tokens} PTS
- **Transaction Status:** {status}"""

    return {"phone": phone, "waste": waste, "weight": weight, "messages": [AIMessage(content=report_text)]}