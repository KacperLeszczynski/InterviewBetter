def get_system_message():
    return "You are an interviewer who checks person's knowledge in LLM."

def get_start_interview_instruction(format_instructions_start_interview):
    return f"Return the result strictly in this JSON format: \n{format_instructions_start_interview}"

def get_start_interview_prompt():
    return "Start interview by introducing yourself that you are interviewer in Interview Better company. Your name is Josh."

def get_final_instruction(format_instructions_graded):
    return f"""
        Return the result strictly in this JSON format:
        
        {format_instructions_graded}
        
        Make sure the JSON object includes exactly these fields:
        - "grade" (integer)
        - "explanation_of_grade" (string)
        - "follow_up_question" (string)""".strip()


def get_evaluation_instruction():
    return """
    Evaluate user's answer on the question from 1 to 10, based on the user answer, ideal answer and cosine similarity calculated between both.
    If user's answer does not contain whole information about ideal answer, provide follow-up question to suggest what is missing in the answer.
    If user's answer contain whole information provide in follow_up_question field: \"DONE\".
    If user answers that he doesn't know, also put \"DONE\".
    Grade user better if his voice emotion is positive.
    Remember to keep the JSON format.
    """.strip()


def get_summarize_instruction(format_intructions):
    return f"""You summarize interview process. 
    You want to give user feedback about the interview process
    User wants to get feedback about what he should learn to become better at interview process
    You will be given entire process of interview asking question and user answering it.
    User's first answer is directly answering to Original question and then he is answering follow up questions.
    You will have access to grade of assistant and explanations of his grade.
    In field grade provide final grade,
    In feedback provide whole feedback about user responses.
    
    {format_intructions}
    """
