import os
from flask import Blueprint, request, current_app, jsonify
from werkzeug.utils import secure_filename

from website_AI import AIPlanner

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

    ai = AIPlanner()
    summary = ai.summarize(path)
    print(summary)
    return {"summary": summary}


@pdf.route("/quiz/generate", methods=["POST"])
def quiz():
    try:
        data = request.get_json(force=True)

        filename   = data.get("filename")
        count      = int(data.get("count", 5))
        difficulty = data.get("difficulty", "medium")

        print("\n========== QUIZ GENERATION ==========")
        print(f"[DEBUG] filename:   {filename}")
        print(f"[DEBUG] count:      {count}")
        print(f"[DEBUG] difficulty: {difficulty}")

        if not filename:
            return jsonify({"error": "No filename provided"}), 400

        upload_folder = current_app.config["UPLOAD_FOLDER"]
        path = os.path.join(upload_folder, filename)

        print(f"[DEBUG] full path:  {path}")
        print(f"[DEBUG] file exists: {os.path.exists(path)}")

        if not os.path.exists(path):
            return jsonify({"error": "File not found"}), 404

        ai = AIPlanner()

        # -------------------------
        # Extract PDF text
        # -------------------------
        pdf_data = ai._load_pdf(path)
        pages = pdf_data["pages"]

        pdf_text = "\n\n".join(
            p["text"].strip() for p in pages if not p["is_empty"]
        )

        print(f"[DEBUG] extracted text length: {len(pdf_text)} chars")
        print(f"[DEBUG] preview: {pdf_text[:200]}")

        if not pdf_text.strip():
            print("[DEBUG] ERROR: empty text extracted")
            return jsonify({"error": "Could not extract text from PDF"}), 400

        # -------------------------
        # LIMIT TEXT (VERY IMPORTANT)
        # -------------------------
        words = pdf_text.split()
        if len(words) > 2000:
            print("[DEBUG] truncating text for quiz...")
            pdf_text = " ".join(words[:2000])

        # -------------------------
        # Generate quiz
        # -------------------------
        print("[DEBUG] calling generate_quiz...")

        try:
            questions = ai.generate_quiz(pdf_text, count, difficulty)
        except Exception as e:
            print("[ERROR] Quiz generation failed:", str(e))
            return jsonify({
                "error": "Quiz generation failed",
                "details": str(e)
            }), 500

        print(f"[DEBUG] questions generated: {len(questions)}")

        if questions:
            for q in questions:
                print(f"[DEBUG] Q{q['id']}: {q['question']}")

        print("=====================================\n")

        return jsonify({"questions": questions})

    except Exception as e:
        print("[FATAL ERROR]", str(e))
        return jsonify({"error": "Server error", "details": str(e)}), 500