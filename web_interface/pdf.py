import os
from flask import Blueprint, request, current_app, jsonify
from werkzeug.utils import secure_filename

pdf = Blueprint('pdf', __name__)

@pdf.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")

    if not file:
        return {"error": "No file"}, 400

    filename = secure_filename(file.filename)

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)

    path = os.path.join(upload_folder, filename)
    file.save(path)

    return {"filename": filename}

@pdf.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    filename = data.get("filename")

    if not filename:
        return {"error": "No filename"}, 400

    upload_folder = current_app.config["UPLOAD_FOLDER"]
    path = os.path.join(upload_folder, filename)

    from .ai import AIPlanner
    ai = AIPlanner()

    summary = ai.summarize(path)

    return {"summary": summary}


# @pdf.route("/qa", methods=["POST"])
# def qa():
#     data = request.json
#     filename = data.get("filename")
#     question = data.get("question")
#
#     if not filename or not question:
#         return {"error": "Missing data"}, 400
#
#     upload_folder = current_app.config["UPLOAD_FOLDER"]
#     path = os.path.join(upload_folder, filename)
#
#     from .ai import AIPlanner
#     ai = AIPlanner()
#
#     answer = ai.ask(path, question)
#
#     return {"answer": answer}