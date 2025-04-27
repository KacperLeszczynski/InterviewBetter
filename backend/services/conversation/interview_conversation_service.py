from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from services import RedisService
from utils import get_start_interview_instruction
from utils.conversation_message_utils import get_start_interview_prompt


class StartInterviewModel:
    pass


class InterviewConversationService:
    def __init__(self, redis_service: RedisService, api_key: str):
        self.redis_service = redis_service
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=api_key)

    def start_interview(self, session_id) -> str:
        parser = PydanticOutputParser(pydantic_object=StartInterviewModel)
        format_instructions_start_interview = self._parse_instruction(parser)
        format_instructions = get_start_interview_instruction(format_instructions_start_interview)
        prompt = get_start_interview_prompt()

        self.redis_service.add_message(session_id, "user", prompt)
        prompt = self._build_prompt_with_instruction(session_id=session_id,
                                                     current_user_prompt=prompt,
                                                     format_instruction=format_instructions)
        chain = prompt | self.llm | parser
        result = chain.invoke({})

        self.redis_service.add_message(session_id, "assistant", result.introduction)

        return result.introduction


    def add_message(self, session_id: str, message: str):
        parser = PydanticOutputParser(pydantic_object=StartInterviewModel)
        introduction = ""
        self.redis_service.add_message(session_id, "assistant", introduction)

    def _parse_instruction(self, parser):
        return parser.get_format_instructions().replace("{", "{{").replace("}", "}}")

    def _build_prompt_with_instruction(
            self, *,
            session_id: str,
            current_user_prompt: str,
            format_instruction: str,
            limit: int = 10,
    ) -> ChatPromptTemplate:
        chat: list[tuple[str, str]] = [("system", )]

        recent = self.redis_service.get_recent_messages(session_id, limit=limit)
        chat.extend((m.role, m.content) for m in recent)

        chat.append(("user", current_user_prompt))
        chat.append(("system", format_instruction))

        return ChatPromptTemplate.from_messages(chat)
