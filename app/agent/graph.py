from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from app.agent.state import AgentState
from app.agent.nodes import call_model, tools

def should_continue(state: AgentState):
    """
    Evaluates the current state to determine the next graph execution node.
    Returns 'action' if the language model invoked a tool call.
    Returns the END node to terminate execution if no tools are called.
    """
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "action"
    return END

# Initialize the workflow utilizing the custom AgentState schema
workflow = StateGraph(AgentState) #[cite: 9]

# Register the primary agent node and the tool execution node
workflow.add_node("agent", call_model) #[cite: 9]
workflow.add_node("action", ToolNode(tools)) #[cite: 9]

# Define the starting point of the graph execution
workflow.set_entry_point("agent") #[cite: 9]

# Configure conditional routing from the agent node based on tool requests
workflow.add_conditional_edges("agent", should_continue, {"action": "action", END: END}) #[cite: 9]

# Route the tool node output back to the agent for subsequent evaluation
workflow.add_edge("action", "agent") #[cite: 9]

# Compile the configured workflow into an executable LangGraph application
app_agent = workflow.compile() #[cite: 9]