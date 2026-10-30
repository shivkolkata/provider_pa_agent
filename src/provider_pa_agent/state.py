from typing import TypedDict, List, Dict, Optional, Any

class ProviderPAState(TypedDict):
    # Identifiers & Context
    order_id: str
    patient_id: str
    member_id: str
    payer_id: str
    
    # Clinical Codes & Inputs
    cpt_codes: List[str]
    cpt_description: str
    icd_codes: List[str]
    icd_description: str
    ordering_provider_npi: str
    
    # Extracted EHR Context
    demographics: Dict[str, Any]
    coverage_details: Dict[str, Any]
    raw_ehr_notes: List[str]
    
    # Policy & Criteria Matching
    is_pa_required: bool
    payer_policy_id: Optional[str]
    required_criteria: List[str]
    retrieved_evidence: Dict[str, Any]
    missing_evidence_gaps: List[str]
    
    # Generated Package & Review
    clinical_rationale_draft: Optional[str]
    authorization_package: Optional[Dict[str, Any]]
    specialist_approved: bool
    specialist_feedback: Optional[str]
    
    # Submission & Async Tracking
    submission_transaction_id: Optional[str]
    payer_status: str  # e.g., "PENDING", "SUBMITTED", "APPROVED", "DENIED", "RFI"
    payer_response_payload: Optional[Dict[str, Any]]
    
    # Audit trail
    audit_log: List[Dict[str, str]]

    denial_analysis: Optional[Dict[str, Any]]