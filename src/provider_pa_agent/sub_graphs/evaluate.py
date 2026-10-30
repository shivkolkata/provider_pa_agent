from langgraph.constants import START, END
from langgraph.graph import StateGraph
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.nodes.evaluate import gather_required_clinical_doc
from dotenv import load_dotenv

def identify_missing_info(state: ProviderPAState):
    missing_gaps = state["missing_evidence_gaps"]
    if missing_gaps:
        return "request_missing_information"
    else:
        return "process_submission_and_tracking"

evaluate_builder = StateGraph(ProviderPAState)
evaluate_builder.add_node("gather_required_clinical_doc", gather_required_clinical_doc)

evaluate_builder.add_edge(START, "gather_required_clinical_doc")
evaluate_builder.add_conditional_edges(
    "gather_required_clinical_doc",
    identify_missing_info,
    {
        "request_missing_information": END,
        "process_submission_and_tracking": END
    }
)