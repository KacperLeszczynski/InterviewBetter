from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI


class TranscriptCorrectorService:
    def __init__(self, api_key: str):
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2, api_key=api_key)

        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You correct technical transcripts."),
            ("human", """You are an expert technical text corrector.  
                Given the input transcript, correct any mistakes related to programming and technical vocabulary.
                The input focuses on LLM application, so keep in mind that vocabulary is directly related to LLMs.
                
                Now correct this transcript:
                \"{transcript}\"""")
        ])

        self.chain = self.prompt | self.llm | StrOutputParser()

    def correct_transcript_with_tech_terms(self, transcript: str) -> str:
        return self.chain.invoke({"transcript": transcript})