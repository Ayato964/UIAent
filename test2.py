import pyautogui
import time

# 少し待つ（ユーザーがフォーカスを合わせる時間）
time.sleep(3)

# テキスト入力（今カーソルがある場所に）
pyautogui.write("日本語の入力は不可能なんだね", interval=0.05)
