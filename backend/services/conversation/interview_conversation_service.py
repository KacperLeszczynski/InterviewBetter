from typing import Dict, Any

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from models import GradedAnswer, StartInterviewModel
from models.final_grade_model import FinalGrade
from services.redis_service import RedisService
from utils import get_start_interview_instruction
from utils.conversation_message_utils import get_start_interview_prompt, get_evaluation_instruction, \
    get_final_instruction, get_summarize_instruction


class InterviewConversationService:
    def __init__(self, redis_service: RedisService, api_key: str):
        self.redis_service = redis_service
        self.llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.1, api_key=api_key)

    def ask_question(self, session_id) -> dict[str, str | None | Any]:
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
        question = self.redis_service.choose_question(session_id)

        return {"introduction": result.introduction, "question": question}

    def add_message(self, *, session_id: str, answer: str, emotion: str, ideal_answer: str, follow_up_question: str,
                    question: str) -> GradedAnswer:
        key_information = (
            f"Original question: {question}\n"
            f"Follow up question (if is not None then user answers to this question): {follow_up_question}\n"
            f"User answer: {answer}\n"
            f"Ideal answer: {ideal_answer}\n"
            f"User's emotion: {emotion}\n"
        )
        self.redis_service.add_message(session_id, "user", key_information)
        current_prompt_human = f"{get_evaluation_instruction()}\n\n{key_information}"

        parser_graded = PydanticOutputParser(pydantic_object=GradedAnswer)
        format_instructions_graded = self._parse_instruction(parser_graded)

        prompt = self._build_prompt_with_instruction(
            session_id=session_id,
            current_user_prompt=current_prompt_human,
            format_instruction=get_final_instruction(format_instructions_graded),
            limit=10,
        )

        chain = prompt | self.llm | parser_graded
        graded: GradedAnswer = chain.invoke({})
        self.redis_service.add_message(session_id, "assistant", self._get_grade_information(graded))
        return graded

    def create_final_grade(self, session_id) -> FinalGrade:
        messages = self.redis_service.get_history(session_id)
        parser_final_grade = PydanticOutputParser(pydantic_object=FinalGrade)
        format_instructions_graded = self._parse_instruction(parser_final_grade)

        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "{instruction}\n\n{history}")
        ])
        chain = prompt_template | self.llm | parser_final_grade
        graded: FinalGrade = chain.invoke({
            "instruction": get_summarize_instruction(format_instructions_graded),
            "history": messages
        })

        return graded


    def _parse_instruction(self, parser):
        formatted_instructions = parser.get_format_instructions()
        return formatted_instructions.replace("{", "{{").replace("}", "}}")

    def _get_grade_information(self, graded_result: GradedAnswer):
        return f"""
            grade: {graded_result.grade}
            explanation of this grade: {graded_result.explanation_of_grade}
            follow up question: {graded_result.follow_up_question}
        """

    def _build_prompt_with_instruction(
            self, *,
            session_id: str,
            current_user_prompt: str,
            format_instruction: str,
            limit: int = 10,
    ) -> ChatPromptTemplate:
        chat: list[tuple[str, str]] = []

        recent = self.redis_service.get_recent_messages(session_id, limit=limit)
        chat.extend((m["role"], m["content"]) for m in recent)

        chat.append(("user", current_user_prompt))
        chat.append(("system", format_instruction))

        return ChatPromptTemplate.from_messages(chat)
