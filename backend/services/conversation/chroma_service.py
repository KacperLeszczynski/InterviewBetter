from pathlib import Path

import chromadb
import torch
from sentence_transformers import SentenceTransformer

from models import ChromaMetadataModel

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PATH_CHROMA = PROJECT_ROOT / "chroma_db"


class ChromaService:
    def __init__(self):
        print(PATH_CHROMA)
        client = chromadb.PersistentClient(path=PATH_CHROMA.as_posix())
        embedding_model = "Snowflake/snowflake-arctic-embed-l-v2.0"

        self.collection = client.get_or_create_collection(name="interview_data")
        self.sentence_model = SentenceTransformer(embedding_model).to(torch.device("cuda"))

    def get_ideal_document(self, *,
                           question: str,
                           user_answer: str) -> str:
        
        metadata = ChromaMetadataModel(question=question)

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
