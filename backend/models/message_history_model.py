from pydantic import BaseModel


class MessageHistoryModel(BaseModel):
    role: str
    content: str
