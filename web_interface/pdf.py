import os
from flask import Blueprint, request, current_app, jsonify
from werkzeug.utils import secure_filename

from web_interface.website_AI import AIPlanner
from .rag import RAGStore
from .extract import extract_text_from_pdf

pdf = Blueprint('pdf', __name__)


_rag_cache: dict[str, RAGStore] = {}


def _get_or_build_rag(filename: str, path: str) -> RAGStore:
    if filename not in _rag_cache:
        print(f"[RAG] Building store for: {filename}")
        pdf_data = extract_text_from_pdf(path)
        store = RAGStore()
        store.build(pdf_data["pages"])
        _rag_cache[filename] = store
        print(f"[RAG] Store ready — {len(store.chunks)} chunks")
    else:
        print(f"[RAG] Cache hit for: {filename}")
    return _rag_cache[filename]


def _get_path(filename: str):
    if not filename:
        return None, (jsonify({"error": "No filename provided"}), 400)
    path = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)
    if not os.path.exists(path):
        return None, (jsonify({"error": "File not found"}), 404)
    return path, None


# =============================================================
@pdf.route("/upload", methods=["POST"])
def upload_pdf():
    file = request.files.get("file")
    if not file:
        return jsonify({"error": "No file"}), 400

    filename = secure_filename(file.filename)
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    path = os.path.join(upload_folder, filename)
    file.save(path)

    try:
        store = _get_or_build_rag(filename, path)
        return jsonify({
            "filename": filename,
            "chunks": len(store.chunks)
        })
    except Exception as e:
        print(f"[ERROR] RAG build failed: {e}")
        return jsonify({"error": "Failed to process PDF", "details": str(e)}), 500


# =============================================================
@pdf.route("/summarize", methods=["POST"])
def summarize():
    data = request.json
    filename = data.get("filename")

    path, err = _get_path(filename)
    if err:
        return err

    try:
        ai = AIPlanner()
        summary = ai.summarize(path)
        return jsonify({"summary": summary})
    except Exception as e:
        print(f"[ERROR] Summarize failed: {e}")
        return jsonify({"error": "Summarization failed", "details": str(e)}), 500


# =============================================================
@pdf.route("/quiz/generate", methods=["POST"])
def quiz():
    data = request.get_json(force=True)
    filename   = data.get("filename")
    count      = int(data.get("count", 5))
    difficulty = data.get("difficulty", "medium")

    print(f"\n[QUIZ] filename={filename} count={count} difficulty={difficulty}")

    path, err = _get_path(filename)
    if err:
        return err

    try:
        store = _get_or_build_rag(filename, path)
        ai = AIPlanner()
        questions = ai.generate_quiz(store, count, difficulty)
        return jsonify({"questions": questions})
    except Exception as e:
        print(f"[ERROR] Quiz generation failed: {e}")
        return jsonify({"error": "Quiz generation failed", "details": str(e)}), 500


# =============================================================
@pdf.route("/qa", methods=["POST"])
def qa():
    data = request.get_json(force=True)
    filename = data.get("filename")
    question = data.get("question")

    print(f"\n[QA] filename={filename} question={question}")

    if not question:
        return jsonify({"error": "No question provided"}), 400

    path, err = _get_path(filename)
    if err:
        return err

    try:
        store = _get_or_build_rag(filename, path)
        ai = AIPlanner()
        answer = ai.answer_question(store, question)
        return jsonify({"answer": answer})
    except Exception as e:
        print(f"[ERROR] QA failed: {e}")
        return jsonify({"error": "QA failed", "details": str(e)}), 500


# =============================================================
@pdf.route("/teachback", methods=["POST"])
def teachback():
    data = request.get_json(force=True)
    filename    = data.get("filename")
    explanation = data.get("explanation")

    print(f"\n[TEACHBACK] filename={filename}")

    if not explanation:
        return jsonify({"error": "No explanation provided"}), 400

    path, err = _get_path(filename)
    if err:
        return err

    try:
        store = _get_or_build_rag(filename, path)
        ai = AIPlanner()
        feedback = ai.answer_teachback(store, explanation)
        return jsonify({"feedback": feedback})
    except Exception as e:
        print(f"[ERROR] Teachback failed: {e}")
        return jsonify({"error": "Teachback failed", "details": str(e)}), 500


# =============================================================
@pdf.route("/clear", methods=["POST"])
def clear_cache():
    data = request.get_json(force=True)
    filename = data.get("filename")
    if filename and filename in _rag_cache:
        del _rag_cache[filename]
        print(f"[RAG] Cache cleared for: {filename}")
    return jsonify({"status": "ok"})