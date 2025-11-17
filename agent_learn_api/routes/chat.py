from flask import Blueprint, request, jsonify
from agent_learn_api import db, socket_io
from agent_learn_api.models.chat import Chat
from agent_learn_api.utils.agent_utils import run_agent
from flask_socketio import emit

chat_bp = Blueprint("chat", __name__)

# --- Add new chat message (REST) ---
@chat_bp.route("/", methods=["POST"])
def add_message():
    data = request.json
    role = data.get("role")
    content = data.get("content")
    workspace_id = data.get("workspace_id")
    user_id = data.get("user_id")

    if not role or not content or not workspace_id:
        return jsonify({"error": "role, content, and workspace_id are required"}), 400

    # Save user message
    chat = Chat(
        role=role,
        content=content,
        workspace_id=int(workspace_id),
        user_id=int(user_id)
    )
    db.session.add(chat)
    db.session.commit()

    # Notify all connected clients
    socket_io.emit("receive_message", {
        "id": chat.id,
        "role": chat.role,
        "content": chat.content,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": chat.created_at.isoformat()
    }, broadcast=True)

    # Run AI agent to generate assistant response
    try:
        response = run_agent(int(workspace_id), int(user_id), content)
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Agent failed: {str(e)}"}), 500

    # Save assistant message
    response_chat = Chat(
        role="assistant",
        content=response,
        workspace_id=int(workspace_id),
        user_id=int(user_id)
    )
    db.session.add(response_chat)
    db.session.commit()

    # Emit assistant message via WebSocket
    socket_io.emit("receive_message", {
        "id": response_chat.id,
        "role": response_chat.role,
        "content": response_chat.content,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": response_chat.created_at.isoformat()
    }, broadcast=True)

    return jsonify({
        "user_message": {
            "id": chat.id,
            "role": chat.role,
            "content": chat.content,
            "created_at": chat.created_at
        },
        "assistant_message": {
            "id": response_chat.id,
            "role": response_chat.role,
            "content": response_chat.content,
            "created_at": response_chat.created_at
        }
    }), 201


# --- Get all chat messages for a workspace ---
@chat_bp.route("/<int:workspace_id>", methods=["GET"])
def get_messages(workspace_id):
    user_id = request.args.get("user_id", type=int)
    query = Chat.query.filter_by(workspace_id=workspace_id)
    if user_id:
        query = query.filter_by(user_id=user_id)

    messages = query.order_by(Chat.created_at.asc()).all()
    return jsonify([
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "workspace_id": m.workspace_id,
            "user_id": m.user_id,
            "created_at": m.created_at.isoformat()
        }
        for m in messages
    ]), 200


# --- Delete all chat messages for a workspace ---
@chat_bp.route("/<int:workspace_id>", methods=["DELETE"])
def delete_messages(workspace_id):
    deleted = Chat.query.filter_by(workspace_id=workspace_id).delete()
    db.session.commit()
    return jsonify({"message": f"{deleted} messages deleted"}), 200


# --- WebSocket event: direct message send (real-time) ---
@socket_io.on("send_message")
def handle_send_message(data):
    role = data.get("role", "user")
    content = data.get("content")
    workspace_id = int(data.get("workspace_id"))
    user_id = int(data.get("user_id", 0))

    # 1️⃣ Store user message
    chat = Chat(role=role, content=content, workspace_id=int(workspace_id), user_id=int(user_id))
    db.session.add(chat)
    db.session.commit()

    message_payload = {
        "id": chat.id,
        "role": chat.role,
        "content": chat.content,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": chat.created_at.isoformat(),
    }

    # Broadcast the user message immediately
    emit("receive_message", message_payload, broadcast=True)

    # 2️⃣ Generate assistant response
    try:
        response_text = run_agent(workspace_id, user_id, content)
    except Exception as e:
        print("Agent error:", e)
        response_text = "⚠️ Error: Agent failed to generate response."

    # 3️⃣ Store assistant reply
    assistant_chat = Chat(
        role="assistant",
        content=response_text,
        workspace_id=int(workspace_id),
        user_id=user_id,
    )
    db.session.add(assistant_chat)
    db.session.commit()

    response_payload = {
        "id": assistant_chat.id,
        "role": assistant_chat.role,
        "content": assistant_chat.content,
        "workspace_id": workspace_id,
        "user_id": user_id,
        "created_at": assistant_chat.created_at.isoformat(),
    }

    # 4️⃣ Emit assistant message too
    emit("receive_message", response_payload, broadcast=True)

