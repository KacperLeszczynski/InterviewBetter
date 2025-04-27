from pydantic import BaseModel


class ChromaMetadataModel(BaseModel):
    difficulty: str
    type_question: str
    question: str
