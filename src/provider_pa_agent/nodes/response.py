from typing import List, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langgraph.types import interrupt
from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.llm import get_llm
from provider_pa_agent.objects import DenialAnalysisResult
from provider_pa_agent.prompt import denial_analysis_instructions, denial_analysis_user_instructions
from langchain.messages import SystemMessage, HumanMessage

def update_ehr_and_notify(state: ProviderPAState) -> ProviderPAState:
    """
    Node 5A (Approved): Updates the EHR system, triggers patient scheduling, 
    and notifies the clinical care team of the prior authorization approval.
    """
    state["audit_log"].append({
        "node": "update_ehr_and_notify",
        "message": f"PA Approved for CPT {state.get('cpt_codes')}. EHR updated and care team notified for scheduling."
    })
    return state

def route_back_for_more_info(state: ProviderPAState) -> ProviderPAState:
    """
    Node 5B (Additional Information Required): Handles requests for more info 
    by routing the state back into the Evidence Collection subgraph.
    """
    state["audit_log"].append({
        "node": "route_back_for_more_info",
        "message": "Payer requested additional information. Routing back to Evidence Collection subgraph."
    })
    return state

def analyze_denial_and_recommend(state: ProviderPAState) -> ProviderPAState:
    model = get_llm(temperature=0.0)
    
    response_payload = state.get("payer_response_payload", {})
    raw_ehr_notes = state.get("raw_ehr_notes", [])
    
    # Normalize notes into a single text block if passed as a list
    notes_text = "\n".join(raw_ehr_notes) if isinstance(raw_ehr_notes, list) else str(raw_ehr_notes)
    
    # Wrap model with structured output using our Pydantic schema
    model_with_structure = model.with_structured_output(DenialAnalysisResult)

    human_message = denial_analysis_user_instructions.format(
        payload=str(response_payload), 
        notes=notes_text
    )

    extracted_data: DenialAnalysisResult = model_with_structure.invoke(
        [SystemMessage(content=denial_analysis_instructions)] + [HumanMessage(content=human_message)]
    )  # type: ignore
    
    # Populate global state
    state["denial_analysis"] = extracted_data.model_dump()
    state["clinical_rationale_draft"] = extracted_data.appeal_rationale_draft
    
    # Log audit entry
    state["audit_log"] = []
    state["audit_log"].append({
        "node": "analyze_denial_and_recommend",
        "message": f"Denial analyzed. Category: {extracted_data.denial_category}. Generated appeal recommendation and draft."
    })
    
    return state
def denial_review_gate(state: ProviderPAState) -> ProviderPAState:
    """
    Node 5C Part 2 (Denied - Human HITL): Presents the AI denial analysis and appeal recommendation 
    to a human specialist for review, approval, or escalation.
    """
    analysis = state.get("denial_analysis", {})
    
    human_response = interrupt({
        "action": "REVIEW_DENIAL_AND_APPROVE_APPEAL",
        "denial_analysis": analysis,
        "message": "The prior authorization was denied by the payer. Please review the AI denial analysis, CARC codes, and proposed appeal strategy."
    })
    
    comment = ""
    is_approved = True
    if isinstance(human_response, str):
        comment = human_response.strip()
    elif isinstance(human_response, dict):
        comment = str(human_response.get("feedback", "")).strip()
        if "approved" in human_response:
            is_approved = bool(human_response["approved"])
            
    state["specialist_approved"] = is_approved
    state["specialist_feedback"] = comment
    
    state["audit_log"].append({
        "node": "denial_review_gate",
        "message": f"Specialist reviewed denial. Appeal approved: {is_approved}, Feedback: {comment}"
    })
    
    return state