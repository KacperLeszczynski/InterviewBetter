from pydantic import BaseModel


class GradedAnswer(BaseModel):
    grade: int = 0
    explanation_of_grade: str = ""
    follow_up_question: str = ""

