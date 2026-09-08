from typing import Annotated, TypedDict, Optional
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class AgentState(TypedDict, total=False): #[cite: 10]
    """
    Defines the schema for the LangGraph state orchestration.
    Maintains the conversational message history through the 'add_messages' reducer.
    Explicitly preserves physical deposit telemetry parameters (phone, waste, weight) 
    across continuous graph iterations to prevent data loss between tool calls.
    """
    messages: Annotated[list[BaseMessage], add_messages] #[cite: 10]
    phone: Optional[str] #[cite: 10]
    waste: Optional[str] #[cite: 10]
    weight: Optional[int] #[cite: 10]