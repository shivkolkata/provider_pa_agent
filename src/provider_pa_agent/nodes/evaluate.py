from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.mcp_servers import PayerRulesMCP, EHREHRMCP
from provider_pa_agent.llm import get_llm
from provider_pa_agent.objects import ClinicalEvidence
from provider_pa_agent.prompt import clinical_evidence_collection_instructions, clinical_evidence_collection_user_instructions
from langchain.messages import SystemMessage, HumanMessage
from langgraph.types import interrupt

def gather_required_clinical_doc(state: ProviderPAState) -> ProviderPAState:

    model = get_llm(temperature=0.0)

    policy_id = state.get("payer_policy_id", "N/A")
    
    required_criteria = state.get("required_criteria", [])
    criteria = "\n".join(f"- {c}" for c in required_criteria) if required_criteria else "No specific criteria provided."

    raw_ehr_notes = state.get("raw_ehr_notes", [])
    
    # Normalize notes into a single text block if passed as a list
    notes_text = "\n".join(raw_ehr_notes) if isinstance(raw_ehr_notes, list) else str(raw_ehr_notes)
    
    # Wrap model with structured output using our Pydantic schema
    model_with_structure = model.with_structured_output(ClinicalEvidence)

    human_message = clinical_evidence_collection_user_instructions.format(policy_id=policy_id, criteria=criteria, notes=notes_text)

    
    extracted_data: ClinicalEvidence = model_with_structure.invoke([SystemMessage(content=clinical_evidence_collection_instructions)] + [HumanMessage(content=human_message)])  # type: ignore
    
    
    # Build chain and invoke
    #chain = prompt | model_with_structure
    #extracted_data: ClinicalCodes = chain.invoke({"raw_notes": notes_text})
    
   # Populate global state
    state["retrieved_evidence"] = [item.model_dump() for item in extracted_data.retrieved_evidence] # type: ignore
    state["missing_evidence_gaps"] = extracted_data.missing_evidence_gaps
    state["clinical_rationale_draft"] = extracted_data.clinical_rationale_draft
    
    # Log audit entry
    state["audit_log"].append({
        "node": "evaluate_clinical_evidence",
        "message": f"Clinical evaluation completed. Found {len(extracted_data.retrieved_evidence)} evidence points and {len(extracted_data.missing_evidence_gaps)} documentation gaps."
    })
    
    return state

def request_missing_information(state: ProviderPAState) -> ProviderPAState:
    """
    Node function (HITL): Triggered when clinical evaluation identifies gaps.
    Pauses execution via interrupt to prompt the human specialist for missing information or documentation,
    then appends human feedback to the clinical record.
    """
    gaps = state.get("missing_evidence_gaps", [])
    
    # LangGraph interrupt for human-in-the-loop intervention
    human_input = interrupt({
        "action": "PROVIDE_MISSING_CLINICAL_DOCUMENTATION",
        "missing_gaps": gaps,
        "message": "Clinical evaluation identified evidence gaps. Please provide additional documentation or notes to proceed."
    })
    
    # human_input is expected to be a dict e.g., {"additional_notes": "Added physical therapy records from outpatient clinic."}
    additional_notes = human_input.get("additional_notes", "No additional notes provided by reviewer.")
    
    # Append the human-provided data to raw ehr notes
    if "raw_ehr_notes" not in state:
        state["raw_ehr_notes"] = []
    state["raw_ehr_notes"].append(f"[HUMAN SPECIALIST ADDENDUM]: {additional_notes}")
    
    # Clear gaps after remediation
    # state["missing_evidence_gaps"] = []
    
    state["audit_log"].append({
        "node": "request_missing_information",
        "message": "Specialist provided missing information addendum. Gaps cleared."
    })
    
    return state

    