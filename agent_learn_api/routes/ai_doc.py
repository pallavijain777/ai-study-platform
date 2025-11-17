import os
from flask import Blueprint, request, jsonify, abort, send_from_directory
from agent_learn_api.models.ai_doc import AIDoc
from agent_learn_api.utils.document_utils import generate_image, generate_pdf
from agent_learn_api import db

ai_doc_bp = Blueprint("ai_doc", __name__)
GENERATED_FOLDER = "D:\\Aarav\\Aarav\\agent-learn\\generated_docs"

@ai_doc_bp.route("/create/", methods=["POST"])
def create_doc():
    data = request.get_json(silent=True) or {}
    
    workspace_id = data.get("workspace_id")
    topic = data.get("topic")
    type = data.get("type")
    user_id = data.get("user_id")
    
    if not workspace_id or not topic or not type:
        return jsonify({"erorr": "All fileds are required"}), 400
    
    if not isinstance(workspace_id, int):
        return jsonify({"error": "Workspace id should be an integer"}), 404
    
    if not isinstance(topic, str):
        return jsonify({"error": "Topic should be a string"})
    
    if type not in ["Image", "PDF"]:
        return jsonify({"error": 'type should be either "Image" or "PDF"'}), 400

    
    try:
        if type == "Image":
            generated = generate_image(topic, workspace_id, 4, (512, 512))
            doc = AIDoc(
                file_name=generated,
                type="Image",
                workspace_id=workspace_id,
                user_id=user_id
            )
            db.session.add(doc)
            db.session.commit()
        else:
            generated = generate_pdf(topic, workspace_id)
            doc = AIDoc(
                file_name=generated,
                type="PDF",
                workspace_id=workspace_id,
                user_id=user_id
            )
            db.session.add(doc)
            db.session.commit()
        docs = AIDoc.query.filter_by(workspace_id=workspace_id).all()
        names = [{"name": n.file_name, "id": n.id} for n in docs]
            
        return jsonify({"names": names}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": e}), 500

@ai_doc_bp.route("/<int:workspace_id>", methods=["GET"])
def get_docs(workspace_id):
    try:
        docs = AIDoc.query.filter_by(workspace_id=workspace_id).all()
        names = [{"name": n.file_name, "id": n.id} for n in docs]
        return jsonify({"names": names}), 200
    except Exception as e:
        return jsonify({"error": e}), 500
    
@ai_doc_bp.route("/<int:ai_doc_id>", methods=["DELETE"])
def delete_docs(ai_doc_id):
    try:
        doc = AIDoc.query.filter_by(id=ai_doc_id)
        if not doc:
            return jsonify({"error": f"Doc {ai_doc_id} not found"}), 404
        db.session.delete(doc)
        db.session.commit()
        return jsonify({"message": f"Doc {ai_doc_id} deleted sucessfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": e}), 500
    
@ai_doc_bp.route("/download/<int:ai_doc_id>/", methods=["GET"])
def download_doc(ai_doc_id):
    doc = db.session.get(AIDoc, ai_doc_id)
    if not doc:
        abort(404, "Document not found")

    file_path = os.path.join(GENERATED_FOLDER, str(doc.workspace_id))
    file_path_2 = os.path.join(file_path, doc.file_name)
    if not os.path.exists(file_path_2):
        abort(404, "File missing on server")

    return send_from_directory(file_path, doc.file_name, as_attachment=True)                                            
      