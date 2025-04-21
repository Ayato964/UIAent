import json
import threading
import tkinter as tk
from tkinter import messagebox
from modules.agent import thinking
from modules.gemini import GeminiClient
from modules.prompt import  JSON_PROMPT, Flash_Prompt, JOB_Prompt
from modules.my_azure import get_client

class UIAIAgent:
    def __init__(self, gemini_reason: GeminiClient, azure_client, w, h):
        self.root = tk.Tk()
        self.root.title("UI Agent Client")
        self.gemini = gemini_reason
        self.azure_client = azure_client
        self.events = dict()
        # 画面の幅と高さを取得
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        # ウィンドウの幅と高さ
        window_width = w
        window_height = h

        # 左下の位置を計算
        x_position = 0
        y_position = screen_height - window_height - 150

        # ウィンドウの位置とサイズを設定
        self.root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")


    def __call__(self, *args, **kwargs):
        # ラベルの作成
        label = tk.Label(self.root, text="質問は何ですか？", font=("Arial", 14))
        label.pack(pady=10)

        # テキスト入力フォームの作成
        entry = tk.Entry(self.root, font=("Arial", 14), width=30)
        entry.pack(pady=10)

        # ボタンの作成
        button = tk.Button(self.root, text="送信",
                           command=lambda : threading.Thread(target=thinking, args=(entry.get(), self.gemini, self.azure_client)).start(), font=("Arial", 14))
        button.pack(pady=10)
        self.root.mainloop()




if __name__ == "__main__":
    with open("./config/token.json", "r") as file:
        data = json.load(file)
        api_key = data["token"]
        gemini_client = GeminiClient(api_key=api_key, model=data["reason"], prompt=Flash_Prompt)
        client = get_client("./config/azure.json")
        print("Gemini Client initialized.")

        UI = UIAIAgent(gemini_client, client, 400, 150)
        UI()