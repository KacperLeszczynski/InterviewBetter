from pydantic import BaseModel


class StartInterviewModel(BaseModel):
    introduction: str