from langgraph.constants import START, END
from langgraph.graph import StateGraph
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.nodes.intake import check_PA_order_and_rules, extract_order_details_and_clinical_context, skip_pa
from dotenv import load_dotenv
from provider_pa_agent.sub_graphs.evaluate import evaluate_builder

load_dotenv()

def route_after_intake(state: ProviderPAState):
    if state["is_pa_required"]:
        return "proceed_to_evaluation"
    else:
        return "skip_pa"

# Build the intake sub-graph builder
intake_builder = StateGraph(ProviderPAState)

intake_builder.add_node("extract_order_details_and_clinical_context", extract_order_details_and_clinical_context)
intake_builder.add_node("check_PA_order_and_rules", check_PA_order_and_rules)
intake_builder.add_node("proceed_to_evaluation", evaluate_builder.compile())
intake_builder.add_node("skip_pa", skip_pa)

intake_builder.add_edge(START, "extract_order_details_and_clinical_context")
intake_builder.add_edge("extract_order_details_and_clinical_context","check_PA_order_and_rules")
intake_builder.add_conditional_edges(
    "check_PA_order_and_rules",
    route_after_intake,
    {
        "proceed_to_evaluation": "proceed_to_evaluation",
        "skip_pa": "skip_pa"
    }
)
intake_builder.add_edge("skip_pa",END)
# Export compiled graph for LangSmith / LangGraph CLI
graph = intake_builder.compile()