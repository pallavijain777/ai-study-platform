import json
from flask import Blueprint, request, jsonify
from agent_learn_api import db
from agent_learn_api.models.quiz import Quiz, QuizResult
from agent_learn_api.models.question import Question
from agent_learn_api.utils.agent_utils import generate_quiz, analylize_quiz, normal_llm_answer

quiz_bp = Blueprint("quiz", __name__)

# --- Create a new quiz (auto-generates questions) ---
@quiz_bp.route("/", methods=["POST"])
def create_quiz():
    data = request.json
    workspace_id = data.get("workspace_id")
    user_id = data.get("user_id")
    title = data.get("title", "Untitled Quiz")
    topic = data.get("topic")
    num_questions = data.get("num_questions", 5)

    print(type(user_id))
    print(type(workspace_id))

    if not workspace_id or not user_id:
        return jsonify({"error": "workspace_id and user_id are required"}), 400

    # ✅ convert safely
    try:
        user_id = int(user_id)
        workspace_id = int(workspace_id)
        num_questions = int(num_questions)
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid ID or question count type"}), 400

    # 1️⃣ Create quiz record
    quiz = Quiz(title=title, user_id=user_id, workspace_id=workspace_id)
    db.session.add(quiz)
    db.session.flush()

    # 2️⃣ Auto-generate questions (if topic is provided)
    questions = []
    if topic:
        try:
            generated = generate_quiz(num_questions, topic, user_id)
            for i, q in enumerate(generated):
                options = q.options
                question = Question(
                    type=q.type or "mcq" if options else "open",
                    text=q.text or q.question or "",
                    options=json.dumps(options or []),
                    correct_answer=q.answer,
                    order_index=i,
                    quiz_id=quiz.id,
                    created_for=user_id,
                )
                db.session.add(question)
                questions.append({
                    "order_index": i,
                    "text": q.text,
                    "type": q.type,
                    "options": q.options,
                    "answer": q.answer,
                })

        except Exception as e:
            db.session.rollback()
            print(e)
            return jsonify({"error": f"Failed to generate questions: {str(e)}"}), 500

    db.session.commit()

    return jsonify({
        "message": "Quiz created successfully",
        "id": quiz.id,
        "title": quiz.title,
        "workspace_id": workspace_id,
        "questions": questions
    }), 201


# --- Get all quizzes for a workspace ---
@quiz_bp.route("/workspace/<int:workspace_id>", methods=["GET"])
def get_quizzes(workspace_id):
    quizzes = Quiz.query.filter_by(workspace_id=workspace_id).order_by(Quiz.created_at.desc()).all()
    return jsonify([
        {
            "id": q.id,
            "title": q.title,
            "created_at": q.created_at,
            "user_id": q.user_id
        }
        for q in quizzes
    ]), 200


# --- Get a quiz and its questions ---
@quiz_bp.route("/<int:quiz_id>", methods=["GET"])
def get_quiz(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return jsonify({
        "id": quiz.id,
        "title": quiz.title,
        "questions": [
            {
                "id": q.id,
                "text": q.text,
                "options": q.options,
                "correct_answer": q.correct_answer,
                "type": q.type
            }
            for q in questions
        ]
    }), 200


# --- Optional alias: /quizzes/<id>/questions ---
@quiz_bp.route("/<int:quiz_id>/questions", methods=["GET"])
def get_quiz_questions(quiz_id):
    quiz = Quiz.query.get(quiz_id)
    if not quiz:
        return jsonify({"error": "Quiz not found"}), 404

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return jsonify([
        {
            "id": q.id,
            "text": q.text,
            "options": q.options,
            "correct_answer": q.correct_answer,
            "type": q.type
        }
        for q in questions
    ]), 200


# --- Submit results for a quiz ---
@quiz_bp.route("/<int:quiz_id>/submit", methods=["POST"])
def submit_quiz(quiz_id):
    data = request.json
    user_id = data.get("user_id")
    answers = data.get("answers", [])

    if not user_id or not answers:
        return jsonify({"error": "user_id and answers are required"}), 400

    try:
        for ans in answers:
            result = QuizResult(
                quiz_id=quiz_id,
                question_id=ans["question_id"],
                user_id=user_id,
                given_answer=ans.get("given_answer"),
                is_correct=ans.get("is_correct", False),
            )
            db.session.add(result)

        db.session.commit()
        return jsonify({"message": "Quiz submitted successfully"}), 201

    except Exception as e:
        db.session.rollback()
        print("Error inserting quiz results:", e)
        return jsonify({"error": str(e)}), 500



# --- Get results of a quiz for a user ---
@quiz_bp.route("/<int:quiz_id>/results/<int:user_id>", methods=["GET"])
def get_results(quiz_id, user_id):
    results = QuizResult.query.filter_by(quiz_id=quiz_id, user_id=user_id).all()
    return jsonify([
        {
            "question_id": r.question_id,
            "given_answer": r.given_answer,
            "is_correct": r.is_correct
        }
        for r in results
    ]), 200


# --- Analyze quiz performance ---
@quiz_bp.route("/<int:quiz_id>/analyze/<int:user_id>", methods=["GET"])
def analyze_quiz_results(quiz_id, user_id):
    analysis = analylize_quiz(quiz_id, user_id)
    return jsonify(analysis), 200


# --- Verify whether an answer is correct (for open/fill questions) ---
@quiz_bp.route("/check/", methods=["POST"])
def check_answers():
    data = request.json
    question = data.get("question")
    answer = data.get("answer")
    response = normal_llm_answer(
    f"""You are an answer verifier.
    Question: {question}
    User Answer: {answer}
    If the user's answer is correct, reply strictly with 'Yes.'
    If it is incorrect, reply strictly with 'No.'
    No explanations, no uncertainty."""
    )
    return jsonify({"response": response}), 200
