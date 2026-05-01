import os

from flask import current_app
from ollama import Client
from web_interface.extract import extract_text_from_pdf
upload_folder = current_app.config["UPLOAD_FOLDER"]


class Config:
    MODEL_NAME = "qwen3:14b"
    TEMPERATURE = 0.8

class AIPlanner:
    def __init__(self, model_name=Config.MODEL_NAME, temperature=Config.TEMPERATURE):
        self.client = Client()
        self.model_name = model_name
        self.temperature = temperature

    def _load_pdf(self, path):
        return extract_text_from_pdf(path)

    def summarize(self, path):
        text = self._load_pdf(path)

        response = self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "Summarize the following text."},
                {"role": "user", "content": text}
            ]
        )

        return response['message']['content']

    def ask(self, path, question):
        text = self._load_pdf(path)

        response = self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "Answer questions based on the document."},
                {"role": "user", "content": f"{text}\n\nQuestion: {question}"}
            ]
        )

        return response['message']['content']


    def answer(self, path, question):
        text = self._load_pdf(path)

        response = self.client.chat(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "you are wall-e a friend for a child answer the question he asked you based"},
                {"role": "user", "content": f"{text}\n\nQuestion: {question}"}
            ]
        )

        return response['message']['content']