import json
import os
import threading
import tkinter as tk
from cProfile import label
from random import sample
from time import sleep
from tkinter import messagebox
from modules.agent import thinking
from modules.gemini import GeminiClient
from modules.prompt import JSON_PROMPT, Flash_Prompt

import pyautogui as pg

class UIAIAgent(tk.Tk):
    def __init__(self, gemini_reason: GeminiClient, gemini_json: GeminiClient, w, h):
        super().__init__()
        self.title("UI Agent Client")
        self.gemini = gemini_reason
        self.gemini_json = gemini_json

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = 0
        y_position = screen_height - h - 150
        self.geometry(f"{w}x{h}+{x_position}+{y_position}")

        self.frames = {}
        for F in (FirstLoadPage, MainPage, ErrorUI):
            frame = F(self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(FirstLoadPage)
        threading.Thread(target=self.load_fc).start()

    def show_frame(self, page_class):
        self.frames[page_class].tkraise()

    def load_fc(self):
        sleep(1)
        os.makedirs("data/screenshots", exist_ok=True)
        path = "data/screenshots/now.png"
        pg.screenshot().save(path)
        try:
            prompt = self.gemini.generate("今までのプロンプトを忘れて、次の質問に回答して「この画面は保険金・給付金査定 WEB 画面システム操作マニュアルかどうかをUIが見つかるかどうかで判断して。"
                                          "またUIが見つかった場合は、<FIND>、ない場合は指示の内容を中断し<ERROR>を<ANSWER>の中で回答して。」", image_path=path, is_save_context=False)

            if "ERROR" in prompt:
                self.show_frame(ErrorUI)
            elif "FIND" in prompt:
                self.show_frame(MainPage)
        except Exception as e:
            self.show_frame(ErrorUI)


class Error(tk.Frame):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)

    def reload(self):
        print("再読み込み")
        self.master.show_frame(FirstLoadPage)
        threading.Thread(target=self.master.load_fc).start()


class ErrorNetwork(Error):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="ネットワークエラーが発生しました。\nGeminiのトークンは正しく設定していますか？", font=("Arial", 14))
        label.pack(pady=20)

        button = tk.Button(self, text="再読み込み", font=("Arial", 14),
                           command=lambda : self.reload())

        button.pack(pady=10)

class ErrorUI(Error):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="査定システムが見つかりません。\n内容を確認して下さい。", font=("Arial", 14))
        label.pack(pady=20)

        button = tk.Button(self, text="再読み込み", font=("Arial", 14),
                           command=lambda : self.reload())

        button.pack(pady=10)

class FirstLoadPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        label = tk.Label(self, text="画面を確認中...", font=("Arial", 14))
        label.pack(pady=20)


class MainPage(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        label = tk.Label(self, text="クレーム番号", font=("Arial", 14))
        label.pack(pady=10)

        entry = tk.Entry(self, font=("Arial", 14), width=30)
        entry.pack(pady=10)

        button = tk.Button(self, text="送信", font=("Arial", 14),
                           command=lambda: threading.Thread(
                               target=thinking,
                               args=(f"PDFとプロンプトを厳守し、{entry.get()}というクレーム番号を検索条件として、査定情報を取得してください。",
                                     master.gemini, master.gemini_json)
                           ).start())
        button.pack(pady=10)

if __name__ == "__main__":
    with open("./config/token.json", "r") as file:
        data = json.load(file)
        api_key = data["token"]
        gemini_client = GeminiClient(api_key=api_key, model=data["reason"], prompt=Flash_Prompt, is_ui_prompt=True)
        gemini_json = GeminiClient(api_key=api_key, model=data["json"], prompt=JSON_PROMPT)
        print("Gemini Client initialized.")

        UI = UIAIAgent(gemini_client, gemini_json, 400, 150)
        UI.mainloop()
