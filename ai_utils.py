import google.generativeai as genai
import os
import random
from config import GEMINI_API_KEY

class AIUtils:
    def __init__(self):
        if GEMINI_API_KEY:
            genai.configure(api_key=GEMINI_API_KEY)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            print("⚠️ GEMINI_API_KEY не найден")
            self.model = None

    def get_diary_response(self, user_message: str, user_name: str = "") -> str:
        if not self.model:
            return "🌿 Спасибо, что поделился. Я записал твои мысли."
        
        prompt = f"""
Ты — Маргарита, психолог. Твой стиль — тёплый, бережный, живой.
Пиши короткими предложениями. Разбивай на строки.
Используй эмодзи: 🌿 🫂 🕯️ 🌊 🌙 (максимум 2-3).
Обращайся на «ты». Будь поддерживающей.
Если уместно — задай вопрос в конце.

Пользователь {user_name} написал: "{user_message}"

Ответь в этом стиле. 3-5 коротких строк.
"""
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "🌙 Спасибо, что делишься. Это важно."

    def get_morning_question(self) -> str:
        questions = [
            "🌿 С каким чувством ты просыпаешься сегодня?",
            "🕯️ Что бы ты хотел(а) сохранить от вчерашнего дня?",
            "🌊 Какое намерение у тебя на сегодня?",
            "🫂 Что сейчас чувствует твоё тело?",
            "🌙 Если бы утро имело цвет — какой он сегодня?"
        ]
        return random.choice(questions)

    def get_evening_reflection(self, user_message: str = "") -> str:
        return "🌙 Этот день был твоим.\nСо всем, что в нём случилось.\nТеперь можно отдохнуть.\nСпокойной ночи."