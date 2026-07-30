from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict

class PrescriptionAgentState(TypedDict):
    raw_transcript: str
    ocr_image_path: Optional[str]
    patient_id: int
    doctor_id: Optional[int]
    dependent_id: Optional[int]
    source: str  # 'doctor_voice' | 'doctor_ocr' | 'patient_ocr'
    recorded_diagnosis: Optional[str]
    medications: List[Dict[str, Any]]
    dietary_advice: Optional[Dict[str, Any]]
    advice: Optional[str]
    follow_up_date: Optional[str]
    visit_summary: Optional[str]
    is_valid: bool
    error_message: Optional[str]

class SpecialtyAgentState(TypedDict):
    symptom_text: str
    patient_location: Optional[Dict[str, float]]
    suggested_specialties: List[str]
    primary_tag: str
    reasoning: str
    confidence_score: float

class RankingAgentState(TypedDict):
    hospitals: List[Dict[str, Any]]
    user_lat: float
    user_lng: float
    priority_weights: Dict[str, float]
    ranked_hospitals: List[Dict[str, Any]]
    reasoning_summary: str

class ContextAgentState(TypedDict):
    patient_phone: int
    current_query: str
    has_timeline: bool
    patient_name: str
    recent_doctor_name: Optional[str]
    recent_visit_date: Optional[str]
    recent_diagnosis: Optional[str]
    recent_medications: List[Dict[str, Any]]
    greeting_message: str
    disclaimer_triggered: bool
