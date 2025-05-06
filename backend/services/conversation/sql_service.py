import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PATH_DB = PROJECT_ROOT / "documents.db"


class SqlService:
    def get_random_questions_by_type(self, search_question_type, limit=2):
        for item in PROJECT_ROOT.iterdir():
            print(item.name)

        conn = sqlite3.connect(PATH_DB)
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT question FROM documents
            WHERE type_question LIKE ?
            ORDER BY RANDOM()
            LIMIT {limit};
        """, (f"%{search_question_type}%",))

        results = cursor.fetchall()
        conn.close()

        questions = [question[0] for question in results]

        return questions
