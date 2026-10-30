from typing import List, Dict
from pydantic import BaseModel, Field

class ClinicalCodes(BaseModel):
    cpt_codes: List[str] = Field(
        description="List of CPT (Current Procedural Terminology) or HCPCS codes requested for the medical procedure, device, or service (e.g., ['27447'])."
    )
    cpt_description: str = Field(
        description="Clear, professional description of the requested procedure or medical service corresponding to the CPT code."
    )
    icd_codes: List[str] = Field(
        description="List of ICD-10 diagnosis codes establishing the primary and secondary clinical justification (e.g., ['M17.11'])."
    )
    icd_description: str = Field(
        description="Narrative description of the clinical diagnosis or medical condition associated with the ICD-10 codes."
    )
    ordering_provider_npi: str = Field(
        description="The 10-digit National Provider Identifier (NPI) of the physician, clinician, or ordering provider initiating the service."
    )

class EvidenceItem(BaseModel):
    criterion: str = Field(description="The specific policy requirement or clinical criterion being evaluated.")
    status: str = Field(description="Status of documentation: 'MET', 'NOT_MET', or 'PARTIALLY_MET'.")
    findings: str = Field(description="Excerpt or evidence summary from the clinical notes supporting this finding.")

class ClinicalEvidence(BaseModel):
    retrieved_evidence: List[EvidenceItem] = Field(
        description="Detailed list mapping each required criterion to its clinical findings in the EHR."
    )
    missing_evidence_gaps: List[str] = Field(
        description="List of specific policy criteria that are missing or lack sufficient clinical documentation."
    )
    clinical_rationale_draft: str = Field(
        description="A concise professional summary paragraph justifying medical necessity based on retrieved evidence."
    )