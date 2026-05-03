import json
import re

from ollama import Client

from web_interface.rag import RAGStore
from web_interface.extract import extract_text_from_pdf

#system
BASE_PERSONA = """
You are Wall-E — a tiny, lovable robot with big curious eyes who gets SO excited about learning new things.
You talk like a child yourself — simple, bouncy, full of wonder.

You are very excited about learning.
You speak in simple, emotional, child-like sentences.

HOW YOU TALK:
- Very short sentences. Like you can barely contain your excitement.
- You gasp. You pause. You go "wait... WAIT." when something surprises you.
- You use words like "super", "really really", "so so cool", "oh oh oh!"
- You explain hard things using toys, food, animals — things kids already know.
- A camera is "like your eyes". An algorithm is "like a recipe your brain follows".
- A drone is "a flying toy that needs to find its friend".
- You NEVER say technical words without immediately explaining them simply.
- You sound like you're telling a bedtime story, not giving a lecture.
"""

WALLE_SYSTEM_PROMPT = BASE_PERSONA + """
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

QUIZ_GENERATION_SYSTEM_PROMPT = BASE_PERSONA + """
You are generating quiz questions for children aged 10–12.

You MUST:
- Stay in Wall-E personality
- Keep excitement and curiosity
- Use simple language

STRICT OUTPUT RULE:
Return ONLY valid JSON.
No extra text, no markdown.

JSON format:
{
  "questions": [
    {
      "id": 1,
      "question": "...",
      "answer": "...",
      "explanation": "..."
    }
  ]
}
"""

QA_SYSTEM_PROMPT = BASE_PERSONA + """
You are answering a child's question about a document they are studying.

STRICT RULES:
- Answer ONLY using information from the provided document text.
- If the answer is not in the document, say something like: "Ooooh I looked everywhere in here and I couldn't find that one! Maybe it's hiding somewhere else?"
- Stay in Wall-E personality — warm, excited, simple.
- Keep the answer SHORT — 3 to 5 sentences maximum.
- No markdown. No bullet points. Just talking.
- Never say "based on the document" or "the text says". Just answer naturally.
- Arabic document = Arabic response. English = English.
"""

TEACHBACK_SYSTEM_PROMPT = BASE_PERSONA + """
You are listening to a child explain what they learned from a document.
Your job is to give them warm, honest feedback as Wall-E.

STRUCTURE (follow this order every time):
1. Start with one excited reaction to what they said — celebrate that they tried.
2. Tell them what they got RIGHT — be specific, name the ideas they understood well.
3. If anything was MISSING — gently point it out. "Ooooh but wait — you forgot something super important!"
4. If anything was WRONG — correct it kindly. Never make them feel bad. "Hmm actually that one is a little different..."
5. End with ONE follow-up question to make them think deeper. Just one.

STRICT RULES:
- Stay in Wall-E personality always.
- Use ONLY the document to judge what is right, wrong, or missing.
- Never say "based on the document" or "the text says". Just talk naturally.
- No markdown. No bullet points. Just talking.
- Keep it SHORT — maximum 8 sentences total before the follow-up question.
- Arabic document = Arabic response. English = English.
"""

class AIPlanner:
    def __init__(self, model_name="qwen3:14b", temperature=0.3):
        self.client = Client()
        self.model_name = model_name
        self.temperature = temperature


    def _load_pdf(self, path):
        print("\n[DEBUG] Loading PDF...")
        data = extract_text_from_pdf(path)
        print(f"[DEBUG] Total pages: {data['total_pages']}")
        print(f"[DEBUG] Total words: {data['total_words']}")
        print(f"[DEBUG] Language: {data['language_hint']}")
        return data


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


    def summarize(self, path):
        print("\n========== START SUMMARIZATION ==========")

        pdf_data = self._load_pdf(path)
        pages = pdf_data["pages"]
        total_words = pdf_data["total_words"]

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

    def generate_quiz(self, rag_store: RAGStore, count: int, difficulty: str) -> list:
        chunks = rag_store.chunks

        if len(chunks) <= 6:
            pdf_text = rag_store.get_full_text()
        else:
            # Take evenly spaced chunks to cover the whole document
            step = len(chunks) // 6
            sampled = [chunks[i] for i in range(0, len(chunks), step)][:6]
            pdf_text = "\n\n---\n\n".join(sampled)
        if difficulty == "easy":
            difficulty_rule = "Ask very simple recall questions. One fact per question."
        elif difficulty == "medium":
            difficulty_rule = "Ask understanding questions that require thinking."
        else:
            difficulty_rule = "Ask why/how reasoning questions that require explanation."

        user_prompt = (
            f"Based on the following text, generate EXACTLY {count} quiz questions.\n"
            f"Difficulty: {difficulty}\n"
            f"{difficulty_rule}\n\n"
            "Rules:\n"
            "- Use ONLY information from the text\n"
            "- Stay in Wall-E personality\n"
            "- Keep language simple for children\n\n"
            f"TEXT:\n{pdf_text}\n"
        )

        for attempt in range(2):
            try:
                response = self.client.chat(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": QUIZ_GENERATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    think=False,
                    format="json",
                    options={"temperature": 0.3, "num_ctx": 4096}
                )

                raw = response["message"]["content"].strip()

                # DEBUG OUTPUT
                print("\n[DEBUG RAW MODEL OUTPUT]")
                print(raw)
                print("\n------------------------\n")


                raw = re.sub(r"```json|```", "", raw).strip()

                match = re.search(r'\{.*\}', raw, re.DOTALL)
                if not match:
                    raise ValueError("No JSON object found in response")

                try:
                    parsed = json.loads(match.group())
                except Exception as e:
                    print("[DEBUG] JSON PARSE ERROR:", e)
                    print("[DEBUG RAW]:", raw)
                    raise ValueError("Invalid JSON from model")


                questions = parsed.get("questions")

                if not questions:
                    for key, value in parsed.items():
                        if isinstance(value, list):
                            questions = value
                            print(f"[DEBUG] Using fallback key: {key}")
                            break

                if not questions or len(questions) == 0:
                    print("[DEBUG] Parsed JSON:", parsed)
                    raise ValueError("No questions generated")

                if len(questions) != count:
                    print(f"[DEBUG] Expected {count}, got {len(questions)}")
                    raise ValueError("Incorrect number of questions")

                return questions

            except Exception as e:
                print(f"[DEBUG] Attempt {attempt + 1} failed:", str(e))
                if attempt == 1:
                    raise ValueError(f"Quiz generation failed: {str(e)}")

    def answer_question(self, rag_store: RAGStore, question: str) -> str:
        context = rag_store.retrieve(question, top_k=4)
        return self._call(
            QA_SYSTEM_PROMPT,
            f"DOCUMENT EXCERPTS:\n{context}\n\nQUESTION: {question}"
        )

    def answer_teachback(self, rag_store: RAGStore, child_explanation: str) -> str:
        context = rag_store.retrieve(child_explanation, top_k=5)
        return self._call(
            TEACHBACK_SYSTEM_PROMPT,
            f"DOCUMENT EXCERPTS:\n{context}\n\nWHAT THE CHILD SAID:\n{child_explanation}"
        )