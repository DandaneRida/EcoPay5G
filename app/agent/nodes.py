import re
from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.tools import tool
from app.camara.client import NokiaNaCClient
from app.agent.state import AgentState

nokia_client = NokiaNaCClient()

@tool
def request_qod_tool(phone_number: str) -> str:
    """CAMARA Tool: Trigger 5G network boost for heavy payload transmissions."""
    res = nokia_client.request_qod(phone_number)
    mode_str = res.get("mode", "UNKNOWN")
    status = res.get("qosStatus", "ACTIVE")
    return f"QOD_BOOST_GRANTED: 5G priority active (Status: {status}). [Mode: {mode_str}]"

# Only the QoD tool remains active in the agent's toolkit
tools = [request_qod_tool]

def parse_deposit_info(messages):
    """Extracts phone number, waste class, and weight from the conversation history."""
    full_text = " ".join([str(getattr(m, 'content', '')) for m in messages])
    phone_match = re.search(r"\+?\d{10,15}", full_text)
    phone = phone_match.group(0) if phone_match else "+358400000001"

    waste_match = re.search(r"Waste=([a-zA-Z]+)", full_text, re.IGNORECASE)
    if waste_match:
        waste = waste_match.group(1).lower()
    else:
        material_search = re.search(r"\b(plastic|glass|metal|paper|cardboard)\b", full_text, re.IGNORECASE)
        waste = material_search.group(1).lower() if material_search else "plastic"

    weight_match = re.search(r"Weight=(\d+)", full_text, re.IGNORECASE)
    if not weight_match:
        weight_match = re.search(r"(\d+)\s*g", full_text, re.IGNORECASE)
    weight = int(weight_match.group(1)) if weight_match else 0
    
    return phone, waste, weight

def calculate_tokens(waste: str, weight: int) -> float:
    """Calculates EcoTokens based on material classification and weight metrics."""
    rates = {
        "plastic": 0.10, 
        "glass": 0.05, 
        "metal": 0.15, 
        "paper": 0.08, 
        "cardboard": 0.07
    }
    return round(weight * rates.get(waste.lower(), 0.10), 2)

def call_model(state: AgentState):
    """
    Executes the logic flow.
    Evaluates the deposit weight and triggers the CAMARA QoD API if the payload is heavy.
    """
    messages = list(state.get("messages", []))
    phone = state.get("phone")
    waste = state.get("waste")
    weight = state.get("weight")

    # Fallback parsing in case state variables are not properly initialized
    if not phone or not waste or weight is None or weight == 0:
        p, wa, we = parse_deposit_info(messages)
        phone, waste, weight = phone or p, waste or wa, weight or we

    # Identify if tools have already been executed during this state graph run
    tool_messages = [m for m in messages if isinstance(m, ToolMessage)]
    has_qod = any("QOD_BOOST" in str(m.content) for m in tool_messages)

    # Trigger QoD request if weight is above 1000g and the tool has not been executed yet
    if weight > 1000 and not has_qod:
        return {
            "phone": phone, 
            "waste": waste, 
            "weight": weight,
            "messages": [
                AIMessage(
                    content="", 
                    tool_calls=[{"name": "request_qod_tool", "args": {"phone_number": phone}, "id": "qod_boost_call"}]
                )
            ]
        }

    # Retrieve output from the QoD tool execution if it was invoked
    qod_output = next((m.content for m in tool_messages if "QOD_BOOST" in str(m.content)), "")
    
    # Determine network status for the final synthesis report
    if weight > 1000:
        qod_status = qod_output.split('[')[0].strip() if qod_output else "Execution Failed"
    else:
        qod_status = "Not Required (Standard Payload)"

    tokens = calculate_tokens(waste, weight)

    # Construct the finalized deposit summary report
    report_text = f"""### Deposit Decision Report
- **5G Network Boost (QoD):** {qod_status}
- **Recycled Material:** {waste.upper()} ({weight}g)
- **EcoTokens Awarded:** {tokens} PTS
- **Transaction Status:** APPROVED"""

    return {
        "phone": phone, 
        "waste": waste, 
        "weight": weight, 
        "messages": [AIMessage(content=report_text)]
    }