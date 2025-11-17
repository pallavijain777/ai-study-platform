import os
import openai
from random import choice
from typing import List, Optional
from dotenv import load_dotenv, find_dotenv
from pydantic import BaseModel, Field
from agent_learn_api.models import QuizResult
from agent_learn_api.models import Question
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

load_dotenv(find_dotenv())

openai.api_key = os.getenv("OPENAI_API_KEY")

model = ChatOpenAI(model="gpt-4o", temperature=0.9)

class QuestionSchema(BaseModel):
    type: str = Field(description="Type of question: mcq, fill in the blank, open")
    text: str = Field(description="Question text")
    options: Optional[List[str]] = Field(default=None, description="Options if MCQ")
    answer: Optional[str] = Field(default=None, description="Correct answer if MCQ")
    question_str: Optional[str] = Field(default=None, description="Concatenation of text and options")
    
parser = PydanticOutputParser(pydantic_object=QuestionSchema)

def generate_questions(topic: str, type: str, user_id: int) -> QuestionSchema:
    '''Returns a question for a topic and a type'''
    prompt_part = """Generate an {type} question on {topic} other than {already_generated}
        {format_instructions}
    """
    already_generated = Question.query.filter_by(created_for=user_id).all()
    prompt = PromptTemplate(
        template=prompt_part,
        input_variables=["type", "topic", "already_generated"],
        partial_variables={"format_instructions": parser.get_format_instructions()}
    )
    chain = prompt | model | parser
    answer = chain.invoke({"type": type, "topic": topic, "already_generated": [q.text for q in already_generated]})
    return answer

def generate_quiz(num_of_questions, topic: str, user_id: int):
    """Generates a quiz of a specified number of questions and a topic"""
    questions = []
    num_of_questions = int(num_of_questions)
    for i in range(num_of_questions):
        q = generate_questions(topic, choice(["MCQ", "Fill in the blanks", "open"]), user_id)
        questions.append(q)
    # sort explicitly by index (safety)
    return questions


def analylize_quiz(quiz_id: int, user_id: int):
    """
    Return score, accuracy and areas of improvement in a quiz
    """
    results = QuizResult.query.filter_by(quiz_id=quiz_id, user_id=user_id).all()
    if not results:
        return {"error": "No results found"}
    
    total = len(results)
    correct = sum(1 for r in results if r.is_correct)
    areas_of_improvement = model.invoke(f"Analyise the quiz results: {results}  of one quiz  ( the is_correct determines whether an answer is correct )and give feedback. The quiz is of 5 questions and the number of correct questions is {correct}").content
    
    return {
        "quiz_id": quiz_id,
        "user_id": user_id,
        "total_questions": total,
        "correct_answers": correct,
        "accuracy": round(correct / total * 100, 2),
        "feedback": areas_of_improvement
    }