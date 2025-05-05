from pydantic import BaseModel


class ChromaMetadataModel(BaseModel):
    difficulty: str = 'easy'
    type_question: str = 'llm'
    question: str = 'What is your name?'
