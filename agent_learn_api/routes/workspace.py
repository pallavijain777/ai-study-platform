from flask import Blueprint, request, jsonify
from agent_learn_api import db
from agent_learn_api.models.workspace import Workspace

workspace_bp = Blueprint("workspace", __name__)

# --- Create workspace ---
@workspace_bp.route("/", methods=["POST"])
def create_workspace():
    data = request.json
    print(data)
    ws = Workspace(name=data["name"], user_id=data["user_id"])
    db.session.add(ws)
    db.session.commit()
    return jsonify({"message": "Workspace created", "id": ws.id, "name": ws.name}), 201


# --- Get all workspaces for a user ---
@workspace_bp.route("/user/<int:user_id>", methods=["GET"])
def get_workspaces(user_id):
    workspaces = Workspace.query.filter_by(user_id=user_id).all()
    return jsonify([
        {"id": ws.id, "name": ws.name}
        for ws in workspaces
    ]), 200


# --- Delete workspace ---
@workspace_bp.route("/<int:workspace_id>", methods=["DELETE"])
def delete_workspace(workspace_id):
    deleted = Workspace.query.filter_by(id=workspace_id).delete()
    db.session.commit()
    return jsonify({"message": f"Workspace {workspace_id} deleted"}), 200
