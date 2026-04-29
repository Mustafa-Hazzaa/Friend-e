import os

from flask import Blueprint, request, current_app
from werkzeug.utils import secure_filename

pdf = Blueprint('pdf', __name__)

@pdf.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")

    if not file:
        return {"error": "No file"}, 400

    filename = secure_filename(file.filename)

    upload_folder = current_app.config["UPLOAD_FOLDER"] = "uploads"
    path = os.path.join(upload_folder, filename)

    file.save(path)

    return {"filename": filename}

@pdf.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    return

@pdf.route("/qa", methods=["POST"])
def qa():
    data = request.json
    return