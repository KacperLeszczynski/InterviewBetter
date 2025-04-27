import chromadb
import torch
from sentence_transformers import SentenceTransformer

from models import ChromaMetadataModel

PATH_CHROMA = "../../chroma_db"


class ChromaService:
    def __init__(self):
        client = chromadb.PersistentClient(path=PATH_CHROMA)
        embedding_model = "Snowflake/snowflake-arctic-embed-l-v2.0"

        self.collection = client.get_or_create_collection(name="interview_data")
        self.sentence_model = SentenceTransformer(embedding_model).to(torch.device("cuda"))

    def get_ideal_document(self, *,
                           difficulty: str,
                           type_question: str,
                           question: str,
                           user_answer: str) -> str:
        
        metadata = ChromaMetadataModel(difficulty=difficulty, type_question=type_question, question=question)

        results = self.collection.query(
            query_embeddings=[self.sentence_model.encode(user_answer, convert_to_numpy=True)],
            n_results=3,
            where={
                "question": metadata.question
            },
            include=["embeddings", "documents", "metadatas", "distances"]
        )

        ideal_answer = results["documents"][0][0]
        return ideal_answer
