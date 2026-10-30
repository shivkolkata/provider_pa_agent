from langgraph.types import interrupt
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.mcp_servers import SubmissionClearinghouseMCP
from provider_pa_agent.llm import get_llm
import json
from provider_pa_agent.prompt import clinical_rational_instructions, clinical_rational_user_instructions
from langchain.messages import SystemMessage, HumanMessage

def process_submission_and_tracking(state: ProviderPAState) -> ProviderPAState:
    """
    Node function: Creates and finalizes the authorization package, submits it via the 
    FHIR PAS / Clearinghouse MCP adapter, and initiates asynchronous tracking.
    """
    # 1. Synthesize the final Prior Authorization package
    authorization_package = {
        "order_id": state.get("order_id"),
        "patient_id": state.get("patient_id"),
        "member_id": state.get("member_id"),
        "payer_id": state.get("payer_id"),
        "cpt_codes": state.get("cpt_codes"),
        "icd_codes": state.get("icd_codes"),
        "ordering_provider_npi": state.get("ordering_provider_npi"),
        "demographics": state.get("demographics", {}),
        "coverage_details": state.get("coverage_details", {}),
        "retrieved_evidence": state.get("retrieved_evidence", {}),
        "clinical_rationale": state.get("clinical_rationale_draft", ""),
        "full_clinical_record": state.get("raw_ehr_notes", [])
    }
    
    state["authorization_package"] = authorization_package
    
    # 2. Submit via Clearinghouse FHIR MCP
    submission_response = SubmissionClearinghouseMCP.submit_pa_package(authorization_package)
    
    state["submission_transaction_id"] = submission_response.get("transaction_id")
    state["payer_status"] = submission_response.get("status", "SUBMITTED")
    state["payer_response_payload"] = submission_response
    
    # 3. Poll async status (simulating immediate or background check)
    txn_id = state["submission_transaction_id"]
    if txn_id:
        status_check = SubmissionClearinghouseMCP.poll_payer_status(txn_id)
        state["payer_status"] = status_check.get("status", state["payer_status"])
        state["payer_response_payload"] = status_check

    state["audit_log"].append({
        "node": "process_submission_and_tracking",
        "message": f"Successfully submitted PA package via FHIR PAS API. Transaction ID: {txn_id}, Status: {state['payer_status']}"
    })
    
    return state

def generate_clinical_rational(state: ProviderPAState) -> ProviderPAState:
    model = get_llm(temperature=0.0)

    # Gather all relevant context from state
    context_payload = {
        "cpt_codes": state.get("cpt_codes"),
        "cpt_description": state.get("cpt_description"),
        "icd_codes": state.get("icd_codes"),
        "icd_description": state.get("icd_description"),
        "ordering_provider_npi": state.get("ordering_provider_npi"),
        "demographics": state.get("demographics"),
        "coverage_details": state.get("coverage_details"),
        "required_criteria": state.get("required_criteria"),
        "retrieved_evidence": state.get("retrieved_evidence"),
        "raw_ehr_notes": state.get("raw_ehr_notes")
    }

    human_message = clinical_rational_user_instructions.format(payload=json.dumps(context_payload, indent=2))

    response = model.invoke([SystemMessage(content=clinical_rational_instructions)] + [HumanMessage(content=human_message)])

    state["clinical_rationale_draft"] = response.content # type: ignore
    
    state["audit_log"].append({
        "node": "generate_clinical_rationale",
        "message": "AI successfully generated comprehensive clinical rationale for payer submission."
    })

    return state

def specialist_review_gate(state: ProviderPAState) -> ProviderPAState:
    """
    Node function (HITL Review Gate): Presents the finalized prior authorization package 
    and AI-generated rationale to a human specialist for final review. 
    Captures specialist approval (`specialist_approved`) and feedback.
    """
    package_to_review = {
        "patient_id": state.get("patient_id"),
        "cpt_codes": state.get("cpt_codes"),
        "cpt_description": state.get("cpt_description"),
        "icd_codes": state.get("icd_codes"),
        "clinical_rationale_draft": state.get("clinical_rationale_draft"),
        "retrieved_evidence": state.get("retrieved_evidence"),
        "coverage_details": state.get("coverage_details")
    }
    
    # LangGraph interrupt for human sign-off
    human_response = interrupt({
        "action": "SPECIALIST_REVIEW_AND_APPROVAL",
        "review_package": package_to_review,
        "message": "Please review the prior authorization package and clinical rationale before submission. If you are ok please say ok/approved/empty/blank, you may also provide feedback"
    })
    
# Flexible parsing of human response (handles raw strings or dicts)
    comment = ""
    is_approved = True  # Default to approved for empty/blank/ok
    
    if isinstance(human_response, str):
        comment = human_response.strip()
    elif isinstance(human_response, dict):
        comment = str(human_response.get("feedback", human_response.get("comment", ""))).strip()
        if "approved" in human_response:
            is_approved = bool(human_response["approved"])
            
    # Dynamic intent analysis on text comment
    if isinstance(human_response, str) or ("approved" not in human_response if isinstance(human_response, dict) else True):
        lower_comment = comment.lower()
        if not comment or any(word in lower_comment for word in ["ok", "approved", "lgtm", "yes", "proceed", "good", "fine"]):
            is_approved = True
        elif any(word in lower_comment for word in ["reject", "deny", "stop", "no", "incorrect", "fix"]):
            is_approved = False
        else:
            is_approved = True  # Treat general comments as approved with notes

    feedback = comment if comment else "No feedback provided (Default Approved)."
    
    # Update state fields
    state["specialist_approved"] = is_approved
    state["specialist_feedback"] = feedback
    
    if "raw_ehr_notes" not in state:
        state["raw_ehr_notes"] = []
    state["raw_ehr_notes"].append(f"[SPECIALIST REVIEW FEEDBACK]: {feedback}")
    
    state["audit_log"].append({
        "node": "specialist_review_gate",
        "message": f"Specialist review completed. Approved: {is_approved}, Feedback: {feedback}"
    })
    
    return state

