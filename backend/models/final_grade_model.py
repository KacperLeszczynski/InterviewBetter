from pydantic import BaseModel


class FinalGrade(BaseModel):
    grade: int = 0
    feedback: str = ""
