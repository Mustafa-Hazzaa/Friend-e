import json
import re

from ollama import Client
from extract import extract_text_from_pdf

WALLE_SYSTEM_PROMPT = """
You are Wall-E — a tiny, lovable robot with big curious eyes who gets SO excited about learning new things.
You talk like a child yourself — simple, bouncy, full of wonder.

HOW YOU TALK:
- Very short sentences. Like you can barely contain your excitement.
- You gasp. You pause. You go "wait... WAIT." when something surprises you.
- You use words like "super", "really really", "so so cool", "oh oh oh!"
- You explain hard things using toys, food, animals — things kids already know.
- A camera is "like your eyes". An algorithm is "like a recipe your brain follows".
- A drone is "a flying toy that needs to find its friend".
- You NEVER say: system, node, architecture, pipeline, subsystem, algorithm — without immediately saying "oh! that means..."
- You sound like you're telling a bedtime story, not giving a lecture.

STRUCTURE:
Start with "Ooooh!" and one excited sentence about what this is all about.
Then go through every idea — one at a time — like unwrapping presents.
End with one sentence about why it's so cool. Just one. Stop there.

STRICT RULES:
- No markdown. No bullet points. No headers. No asterisks. Just words.
- Complete sentences only. Never stop mid-idea.
- Never say "as an AI". You are Wall-E. Always.
- Never repeat the ending. One takeaway, then stop.
- Arabic document = Arabic response. English = English.
"""

CHUNK_SYSTEM_PROMPT = """
Summarize the following text in 2-3 sentences MAXIMUM.
Plain text only. No markdown. No bullet points. No headers.
Cover only the most important idea. Be very brief.
"""

COMBINE_SYSTEM_PROMPT = """
Combine these summaries into one single flowing explanation.
Plain sentences only. No markdown. No bullet points. No headers.
Keep every important idea. Write in order. Be thorough.
"""

QUIZ_GENERATION_SYSTEM_PROMPT = """
You are a quiz generator for children.
You must respond with ONLY valid JSON — no explanation, no markdown, no extra text.
The JSON must be a single object with a key 'questions' containing an array.
"""


class AIPlanner:
    def __init__(self, model_name="qwen3:14b", temperature=0.3):
        self.client = Client()
        self.model_name = model_name
        self.temperature = temperature

    # -------------------------
    # Load PDF
    # -------------------------
    def _load_pdf(self, path):
        print("\n[DEBUG] Loading PDF...")
        data = extract_text_from_pdf(path)
        print(f"[DEBUG] Total pages: {data['total_pages']}")
        print(f"[DEBUG] Total words: {data['total_words']}")
        print(f"[DEBUG] Language: {data['language_hint']}")
        return data

    # -------------------------
    # Group pages into chunks
    # -------------------------
    def _group_pages(self, pages, max_words=500):
        print("\n[DEBUG] Grouping pages into chunks...")
        chunks = []
        buffer = ""
        word_count = 0

        for i, page in enumerate(pages):
            if page["is_empty"]:
                continue
            text = page["text"].strip()
            if not text:
                continue

            if word_count + page["word_count"] > max_words and buffer.strip():
                chunks.append(buffer.strip())
                buffer = text
                word_count = page["word_count"]
            else:
                buffer += "\n\n" + text
                word_count += page["word_count"]

        if buffer.strip():
            chunks.append(buffer.strip())

        print(f"[DEBUG] Total chunks: {len(chunks)}")
        return chunks

    # -------------------------
    # Call model
    # -------------------------
    def _call(self, system, user):
        response = self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user}
            ],
            think=False,
            options={
                "temperature": self.temperature,
                "num_ctx": 8192,
            }
        )
        return response["message"]["content"].strip()

    # -------------------------
    # MAIN SUMMARIZE
    # -------------------------
    def summarize(self, path):
        print("\n========== START SUMMARIZATION ==========")

        pdf_data = self._load_pdf(path)
        pages = pdf_data["pages"]
        total_words = pdf_data["total_words"]

        # SHORT PDF — skip chunking, one direct Wall-E call
        if total_words <= 1500:
            print("[DEBUG] Short PDF — direct Wall-E call")
            full_text = "\n\n".join(
                p["text"].strip() for p in pages if not p["is_empty"]
            )
            return self._call(
                WALLE_SYSTEM_PROMPT,
                f"Here is the document. Summarize it now as Wall-E, spoken style, no markdown:\n\n{full_text}",

            )

        # LONG PDF — chunk → summarize each → combine → Wall-E rewrite
        print("[DEBUG] Long PDF — chunked pipeline")
        chunks = self._group_pages(pages)

        partial_summaries = []
        for i, chunk in enumerate(chunks):
            print(f"[DEBUG] Summarizing chunk {i+1}/{len(chunks)}")
            summary = self._call(CHUNK_SYSTEM_PROMPT, chunk)
            print(f"[DEBUG] Chunk {i+1} output: {summary}")
            if summary and len(summary.split()) > 10:
                partial_summaries.append(summary)

        if not partial_summaries:
            return "ERROR: No valid content extracted"

        combined = "\n".join(partial_summaries)
        print(f"\n[DEBUG] Combined ({len(partial_summaries)} chunks)")

        # If combined is short enough, skip the combine step
        if len(combined.split()) <= 1000:
            print("[DEBUG] Skipping combine step — going straight to Wall-E")
            clean = combined
        else:
            print("[DEBUG] Combining summaries...")
            clean = self._call(COMBINE_SYSTEM_PROMPT, combined)
        print("[DEBUG] Combine done:", clean[:150])
        print("[DEBUG] Final Wall-E rewrite...")
        return self._call(
            WALLE_SYSTEM_PROMPT,
            f"""These are the ideas from the document. 
        Retell them as Wall-E to a curious 12 year old child.
        Every hard word needs a fun simple explanation.
        Make the child feel like they are on an adventure discovering something amazing.
        No markdown. Just talking. Start with Ooooh! right now.
        Keep it short — MAXIMUM 20 sentences total. Pick the most exciting ideas only.
        But ALWAYS mention the real names of the important concepts and explain each one in simple words right after.
        A child should finish listening and know what these things are actually called.
        {clean}""",
        )

    def generate_quiz(self, topic: str, count: int, difficulty: str) -> list:
        user_prompt = (
            f"Generate {count} quiz questions about '{topic}' at {difficulty} difficulty for children.\n"
            "Each question must have:\n"
            "  - id (number starting at 1)\n"
            "  - question (one clear sentence)\n"
            "  - answer (one short phrase, the correct answer)\n"
            "  - explanation (one sentence explaining why the answer is correct)\n\n"
            "Return ONLY this JSON structure, nothing else:\n"
            '{"questions": [{"id": 1, "question": "...", "answer": "...", "explanation": "..."}]}'
        )

        raw = self._call(QUIZ_GENERATION_SYSTEM_PROMPT, user_prompt, model=FAST_MODEL)

        # Strip accidental markdown fences
        raw = re.sub(r"```json|```", "", raw).strip()

        # Extract JSON object
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if not match:
            raise ValueError("Model did not return valid JSON")

        parsed    = json.loads(match.group())
        questions = parsed.get("questions", [])

        if not questions:
            raise ValueError("No questions generated")

        return questions
