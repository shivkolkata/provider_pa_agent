from provider_pa_agent.state import ProviderPAState
from provider_pa_agent.mcp_servers import PayerRulesMCP, EHREHRMCP
def trigger_and_injest_request(state: ProviderPAState) -> ProviderPAState:
    order_id = state['order_id']
    primary_request_data = EHREHRMCP.get_PA_request_primary_data(order_id=order_id)
    
    patient_id = primary_request_data.get("patient_id")
    if not isinstance(patient_id, str) or not patient_id:
        raise ValueError("EHR request data is missing a valid patient_id")
    state["patient_id"] = patient_id

    payer_id = primary_request_data.get("payer_id")
    if not isinstance(payer_id, str) or not payer_id:
        raise ValueError("EHR request data is missing a valid payer_id")
    state["payer_id"] = payer_id

    member_id = primary_request_data.get("member_id")
    if not isinstance(member_id, str) or not member_id:
        raise ValueError("EHR request data is missing a valid member_id")
    state["member_id"] = member_id
    
    return state

def patient_and_coverage_context(state: ProviderPAState) -> ProviderPAState:
    """
    Node function: Retrieves patient demographics, comprehensive clinical notes/context,
    and Payer coverage/benefit details via MCP servers, then populates the state.
    """
    patient_id = state.get("patient_id")
    payer_id = state.get("payer_id")
    member_id = state.get("member_id")
    
    # 1. Fetch patient demographics from EHR MCP
    demographics = EHREHRMCP.fetch_patient_demographics(patient_id)
    
    # 2. Fetch coverage and benefit context from Payer Rules MCP
    coverage_context = PayerRulesMCP.get_coverage_context(payer_id, member_id)
    
    # 3. Fetch comprehensive clinical context / progress notes
    clinical_notes = EHREHRMCP.fetch_clinical_context(patient_id)
    
    # Update the state fields
    state["demographics"] = demographics
    state["coverage_details"] = coverage_context
    state["raw_ehr_notes"] = clinical_notes
    
    # Audit log entry
    state.setdefault("audit_log", [])
    state["audit_log"].append({
        "node": "patient_and_coverage_context",
        "message": f"Retrieved coverage context for plan '{coverage_context.get('plan_name')}' and loaded EHR clinical context."
    })
    
    return state

