from langgraph.constants import START, END
from langgraph.graph import StateGraph
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.nodes.submission import process_submission_and_tracking, generate_clinical_rational, specialist_review_gate
from dotenv import load_dotenv

submission_builder = StateGraph(ProviderPAState)

# add all the nodes
submission_builder.add_node("process_submission_and_tracking", process_submission_and_tracking)
submission_builder.add_node("generate_clinical_rational", generate_clinical_rational)
submission_builder.add_node("specialist_review_gate", specialist_review_gate)

submission_builder.add_edge(START, "generate_clinical_rational")
submission_builder.add_edge("generate_clinical_rational", "specialist_review_gate")
submission_builder.add_edge("specialist_review_gate", "process_submission_and_tracking")
submission_builder.add_edge("process_submission_and_tracking", END)

graph = submission_builder.compile()