import os
from flask import Blueprint, request, jsonify, abort
from flask.helpers import send_file
from werkzeug.utils import secure_filename
from agent_learn_api import db
from agent_learn_api.models.document import Document
from agent_learn_api.utils.document_utils import add_to_index

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

document_bp = Blueprint("document", __name__)


# --- Upload document or image ---
@document_bp.route("/", methods=["POST"])
def upload_document():
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]
    workspace_id = request.form.get("workspace_id")

    if not workspace_id:
        return jsonify({"error": "workspace_id is required"}), 400

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_DIR, filename)
    file.save(file_path)

    try:
        # Index file (text or image)
        add_to_index(file_path, int(workspace_id))

        # Save metadata in DB
        doc = Document(
            filename=filename,
            file_path=file_path,
            workspace_id=workspace_id
        )
        db.session.add(doc)
        db.session.commit()

        return jsonify({
            "message": "Document uploaded and indexed",
            "id": doc.id,
            "filename": doc.filename,
            "file_path": doc.file_path
        }), 201

    except Exception as e:
        db.session.rollback()
        print(e)
        return jsonify({"error": str(e)}), 500


# --- Get all documents ---
@document_bp.route("/<int:workspace_id>", methods=["GET"])
def get_documents(workspace_id):
    docs = Document.query.filter_by(workspace_id=workspace_id).order_by(Document.uploaded_at.desc()).all()
    if not docs:
        return jsonify([])
    return jsonify([
        {
            "id": d.id,
            "filename": d.filename,
            "file_path": d.file_path,
            "uploaded_at": d.uploaded_at
        }
        for d in docs
    ]), 200


# --- Delete a document ---
@document_bp.route("/<int:doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    doc = Document.query.get(doc_id)
    if not doc:
        return jsonify({"error": f"Document {doc_id} not found"}), 404

    db.session.delete(doc)
    db.session.commit()
    return jsonify({"message": f"Document {doc_id} deleted"}), 200


# --- Get Preview ---
@document_bp.route("/preview", methods=["POST"])
def get_preview():
    data = request.get_json()
    filename = data.get("path")

    if not filename:
        return jsonify({"error": "Missing 'path'"}), 400

    # absolute normalized upload folder and file path
    upload_dir_abs = os.path.abspath(UPLOAD_DIR)
    file_path = os.path.realpath(os.path.join(upload_dir_abs, filename))

    # ✅ secure path check
    if not file_path.startswith(upload_dir_abs):
        return jsonify({"error": "Forbidden: outside upload directory"}), 403

    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    from mimetypes import guess_type
    mime_type, _ = guess_type(file_path)
    return send_file(file_path, mimetype=mime_type or "application/octet-stream")
