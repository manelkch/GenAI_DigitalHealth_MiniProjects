from dataclasses import dataclass
from typing import Literal, Optional

UrgencyLevel = Literal["low", "medium", "high"]

@dataclass
class PreDiagnosis:
    condition: str
    urgencyLevel: UrgencyLevel
    symptoms: str

@dataclass
class PatientRequest:
    name: str
    symptoms: str
    temperature: float
    tension: str
    beat_rate: int
    prediagnosis: PreDiagnosis