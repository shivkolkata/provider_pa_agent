from langgraph.constants import START, END
from langgraph.graph import StateGraph
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.nodes.response import (
    update_ehr_and_notify,
    route_back_for_more_info,
    analyze_denial_and_recommend,
    denial_review_gate
)

def route_payer_decision(state: ProviderPAState) -> str:
    """Conditional router based on payer adjudication status."""
    status = state.get("payer_status", "").upper()
    if "APPROV" in status:
        return "approved"
    elif "ADDITIONAL" in status or "PENDING" in status or "INFO" in status:
        return "additional_info"
    else:
        return "denied"

# Build Response Handling sub-graph
builder = StateGraph(ProviderPAState)

# Add nodes
builder.add_node("update_ehr_and_notify", update_ehr_and_notify)
builder.add_node("route_back_for_more_info", route_back_for_more_info)
builder.add_node("analyze_denial_and_recommend", analyze_denial_and_recommend)
builder.add_node("denial_review_gate", denial_review_gate)

# Add conditional routing from START based on payer decision
builder.add_conditional_edges(
    START,
    route_payer_decision,
    {
        "approved": "update_ehr_and_notify",
        "additional_info": "route_back_for_more_info",
        "denied": "analyze_denial_and_recommend"
    }
)

# Wire terminal edges
builder.add_edge("update_ehr_and_notify", END)
builder.add_edge("route_back_for_more_info", END)
builder.add_edge("analyze_denial_and_recommend", "denial_review_gate")
builder.add_edge("denial_review_gate", END)

graph = builder.compile()