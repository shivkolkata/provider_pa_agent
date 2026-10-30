from langgraph.constants import START, END
from langgraph.graph import StateGraph
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.nodes.request import trigger_and_injest_request, patient_and_coverage_context
from provider_pa_agent.sub_graphs.intake import intake_builder

# Build the intake sub-graph builder
builder = StateGraph(ProviderPAState)

builder.add_node("trigger_and_injest_request", trigger_and_injest_request)
builder.add_node("patient_and_coverage_context", patient_and_coverage_context)
builder.add_node("intake_and_eligibility", intake_builder.compile())

builder.add_edge(START, "trigger_and_injest_request")
builder.add_edge("trigger_and_injest_request", "patient_and_coverage_context")
builder.add_edge("patient_and_coverage_context", "intake_and_eligibility")
builder.add_edge("intake_and_eligibility", END)


# Export compiled graph for LangSmith / LangGraph CLI
graph = builder.compile()