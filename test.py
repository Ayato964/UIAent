import json
import os
import pyautogui as pg
from mouseinfo import screenshot
from pymsgbox import prompt

from modules.agent import action,text_to_json, thinking
from modules.gemini import GeminiClient

def textGem():
    is_runninng = True

    while is_runninng:
        input_text = input("あなたの質問をどうぞ: ")
        if input_text.lower() == "exit":
            print("終了します")
            is_runninng = False
        else:
            prompt = gemini_client.generate(input_text=input_text, is_save_context=False)

if __name__ == "__main__":
    with open("./config/token.json", "r") as file:
        data = json.load(file)
        api_key =   data["token"]

        gemini_client = GeminiClient(api_key=api_key, model=data["reason"], prompt="PDFに対する質疑に対し、正確に回答せよ", is_ui_prompt=True)
        print("Gemini Client initialized.")
        textGem()


