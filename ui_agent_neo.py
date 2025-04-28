import json
import os
import threading
import tkinter as tk
from cProfile import label
from random import sample
from time import sleep
from tkinter import messagebox
from modules.agent import thinking,  _THINKING, _ERROR, _ACTION, _WAITING, _CONVERT
from modules.gemini import GeminiClient
from modules.prompt import JSON_PROMPT, Simple_Prompt
from modules.my_azure import get_client

import pyautogui as pg

class UIStatesManager:
    def __init__(self, direct):
        self.states = -1
        self.save_directory = direct

class UIAIAgent(tk.Tk):
    def __init__(self, gemini_reason: GeminiClient, azure_client, w, h,):
        super().__init__()
        self.title("UI Agent Client")
        self.gemini = gemini_reason
        self.azure_client = azure_client
        self.manager = UIStatesManager("./out/")

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x_position = 0
        y_position = screen_height - h - 150
        self.geometry(f"{w}x{h}+{x_position}+{y_position}")

        self.frames = {}
        for F in (FirstLoadPage, MainPage, ErrorUI, ThinkingMenu, ErrorMenu, ActionMenu, ConvertMenu):
            frame = F(self)
            self.frames[F] = frame
            frame.place(relwidth=1, relheight=1)

        self.show_frame(FirstLoadPage)
        threading.Thread(target=self.load_fc).start()
        threading.Thread(target=self.main).start()

    def main(self):
        is_running = True
        stat = self.manager.states
        while is_running:
            if stat != self.manager.states:
                if self.manager.states == _THINKING:
                    self.show_frame(ThinkingMenu)
                if self.manager.states == _ERROR:
                    self.show_frame(ErrorMenu)
                if self.manager.states == _ACTION:
                    self.show_frame(ActionMenu)
                if self.manager.states == _CONVERT:
                    self.show_frame(ConvertMenu)
                if self.manager.states == _WAITING:
                    self.show_frame(MainPage)
                stat = self.manager.states


    def show_frame(self, page_class):
        self.frames[page_class].tkraise()

    def load_fc(self):
        sleep(1)
        os.makedirs("data/screenshots", exist_ok=True)
        path = "data/screenshots/now.png"
        pg.screenshot().save(path)
        try:
            prompt = self.gemini.generate("質問です。この画面は保険金・給付金査定 WEB 画面システム操作マニュアルのUIですか？"
                                          "またUIが見つかった場合は、<FIND>、ない場合は指示の内容を中断し<ERROR>と表示して", image_path=path, is_save_context=False)

            if "ERROR" in prompt:
                self.show_frame(ErrorUI)
            elif "FIND" in prompt:
                self.show_frame(MainPage)
            print("---------------------------------------")
        except Exception as e:
            self.show_frame(ErrorUI)

class ConvertMenu(tk.Frame):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="推論を開始しています。。。",
                         font=("Arial", 14))
        label.pack(pady=20)


class ThinkingMenu(tk.Frame):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="推論を開始しています。。。",
                         font=("Arial", 14))
        label.pack(pady=20)


class ErrorMenu(tk.Frame):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="実行中に不具合が発生しました。\n やり直します。",
                         font=("Arial", 14))
        label.pack(pady=20)

class ActionMenu(tk.Frame):
    def __init__(self, master: UIAIAgent):
        super().__init__(master)
        label = tk.Label(self, text="エージェントを操作しています。。",
                         font=("Arial", 14))
        label.pack(pady=20)



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
                               args=(f"{entry.get()}",
                               #args=("この画面の内容を全てテキストに起こしてください。",
                                     master.gemini, master.azure_client, master.manager)
                           ).start())

        button.pack(pady=10)

if __name__ == "__main__":
    with open("./config/token.json", "r") as file:
        data = json.load(file)
        api_key = data["token"]
        gemini_client = GeminiClient(api_key=api_key, model=data["reason"], prompt=Simple_Prompt, is_ui_prompt=True)
        client = get_client("./config/azure.json")
        print("Gemini Client initialized.")

        UI = UIAIAgent(gemini_client, client, 400, 150)
        UI.mainloop()
