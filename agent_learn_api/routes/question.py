from flask import Blueprint, request, jsonify
from agent_learn_api import db
from agent_learn_api.models.question import Question

question_bp = Blueprint("question", __name__)

# --- Add question ---
@question_bp.route("/", methods=["POST"])
def add_question():
    data = request.json
    q = Question(
        type=data["type"],
        text=data["text"],
        options=data.get("options"),
        answer=data.get("answer"),
        workspace_id=data["workspace_id"],
        created_for=data["created_for"]
    )
    db.session.add(q)
    db.session.commit()
    return jsonify({"message": "Question added", "id": q.id}), 201


# --- Get all questions for a workspace ---
@question_bp.route("/<int:workspace_id>", methods=["GET"])
def get_questions(workspace_id):
    questions = Question.query.filter_by(workspace_id=workspace_id).all()
    return jsonify([
        {
            "id": q.id,
            "type": q.type,
            "text": q.text,
            "options": q.options,
            "answer": q.answer
        }
        for q in questions
    ]), 200


# --- Delete question ---
@question_bp.route("/<int:question_id>", methods=["DELETE"])
def delete_question(question_id):
    deleted = Question.query.filter_by(id=question_id).delete()
    db.session.commit()
    return jsonify({"message": f"Question {question_id} deleted"}), 200
