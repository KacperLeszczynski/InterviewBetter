from typing import List

from pydantic import BaseModel


class InterviewGradeModel(BaseModel):
    grade: int = 0
    feedbacks: List[str] = []