from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.mcp_servers import PayerRulesMCP, EHREHRMCP
from provider_pa_agent.llm import get_llm
from provider_pa_agent.objects import ClinicalCodes
from provider_pa_agent.prompt import clinical_coding_instructions, clinical_coding_user_instructions
from langchain.messages import SystemMessage, HumanMessage

def extract_order_details_and_clinical_context(state: ProviderPAState) -> ProviderPAState:
    """
    Node function: Ingests unstructured EHR notes from state, utilizes the centralized LLM 
    with structured output to parse clinical codes and provider details, and updates the state.
    """
    model = get_llm(temperature=0.0)
    raw_ehr_notes = state.get("raw_ehr_notes", [])
    
    # Normalize notes into a single text block if passed as a list
    notes_text = "\n".join(raw_ehr_notes) if isinstance(raw_ehr_notes, list) else str(raw_ehr_notes)
    
    # Wrap model with structured output using our Pydantic schema
    model_with_structure = model.with_structured_output(ClinicalCodes)

    # System Mess
    #system_message = analyst_instructions.format(topic=topic, max_analysts=max_analysts, human_analyst_feedback=human_feedback)

    human_message = clinical_coding_user_instructions.format(raw_notes=notes_text)
    
    extracted_data: ClinicalCodes = model_with_structure.invoke([SystemMessage(content=clinical_coding_instructions)] + [HumanMessage(content=human_message)]) # type: ignore
    
    
    # Build chain and invoke
    #chain = prompt | model_with_structure
    #extracted_data: ClinicalCodes = chain.invoke({"raw_notes": notes_text})
    
    # Populate state fields with extracted structured data
    state["cpt_codes"] = extracted_data.cpt_codes
    state["cpt_description"] = extracted_data.cpt_description
    state["icd_codes"] = extracted_data.icd_codes
    state["icd_description"] = extracted_data.icd_description
    state["ordering_provider_npi"] = extracted_data.ordering_provider_npi
    
    # Record audit log entry
    state["audit_log"].append({
        "node": "extract_order_details_and_clinical_context",
        "message": f"Successfully extracted clinical codes: CPT {extracted_data.cpt_codes}, ICD {extracted_data.icd_codes} for Provider NPI {extracted_data.ordering_provider_npi}"
    })
    
    return state

def check_PA_order_and_rules(state: ProviderPAState) -> ProviderPAState:
    """
    Node function: Checks if Prior Authorization is required for the ordered CPT code,
    and fetches patient demographics and EHR clinical notes.
    """
    cpt = state["cpt_codes"][0] if state["cpt_codes"] else ""
    payer = state["payer_id"]
    
    # Check rule via MCP
    rule_result = PayerRulesMCP.check_pa_requirement(payer, cpt)
    
    # Fetch EHR demographics & notes
    demographics = EHREHRMCP.fetch_patient_demographics(state["patient_id"])
    notes = EHREHRMCP.fetch_clinical_context(state["patient_id"])
    
    state["is_pa_required"] = rule_result["requires_pa"]
    state["payer_policy_id"] = rule_result["policy_id"]
    state["required_criteria"] = rule_result["required_criteria"]
    state["demographics"] = demographics
    state["raw_ehr_notes"] = notes
    
    # Audit log entry
    state["audit_log"].append({
        "node": "check_order_and_rules",
        "message": f"Checked PA requirement for CPT {cpt}: Required={rule_result['requires_pa']}"
    })
    return state

def skip_pa(state: ProviderPAState) -> ProviderPAState:
        # Audit log entry
    state["audit_log"].append({
        "node": "check_order_and_rules",
        "message": f"PA not required or not eligible"
    })
    return state