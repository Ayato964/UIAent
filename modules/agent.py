import json
import os
import re
from time import sleep
from .my_azure import find_text_position, get, get2
import pyautogui as pg
import pyperclip as cp

STATES =0

_WAITING =1
_THINKING =2
_ACTION = 3
_CONVERT = 4


_ERROR =-1


def _duble_click(target: dict):
    """
    中点を求める
    :param target:
    :return:
    """

    _move(target)

    print("マウスにダブルクリックさせています。。。。")
    pg.doubleClick( button="left")

def _click(target: dict):
    """
    中点を求める
    :param target:
    :return:
    """

    _move(target)
    print("マウスにクリックさせています。")
    pg.click( button="left")

def _move(target: dict):
    print("マウスを移動させています。。。")
    pg.moveTo(target["position"][0], target["position"][1], duration=0.5)


def _type(target: dict):
    input_text = target["input_text"]
    target["position"][1] = target["position"][1] + 25
    _click(target)

    print("テキストを入力しています")
    #pg.write(input_text, interval=1)
    cp.copy(input_text)
    sleep(0.5)
    pg.hotkey('ctrl', 'v')


def action(json_data: dict):
    """
    Perform the action specified in the JSON data.
    """
    print("受信完了。処理を開始します。")
    action_type = json_data["action"]
    target = json_data

    if action_type == "click":
        _click(target)
        pass
    elif action_type == "double_click":
        _duble_click(target)
        pass
    elif action_type == "type":
        _type(target)

    elif action_type == "position":
        # Move mouse to specified position
        pass
    else:
        print("Unknown action type")
    print("処理が完了しました。")


def text_to_json(text, act: str, input_text):
    """
    Convert text to JSON format.
    """
    act_json = dict()
    act_json["action"] = act
    act_json["position"] = text
    if input_text is not None:
        act_json["input_text"] = input_text


    return act_json

def convert_text_file(manager, text):
    directory = manager.save_directory
    if not os.path.exists(directory):
        os.makedirs(directory)

    file_path = os.path.join(directory, "converted_text.txt")
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"テキストをファイルに保存しました: {file_path}")
    except Exception as e:
        print(f"ファイル書き込みエラー: {e}")


def thinking(input_text: str, gemini_reason, azure_client, manager=None):

    manager.states = _THINKING
    claim = get2(azure_client, "クレーム番号", 0.43, 0.61)


    _type({"position": claim, "input_text": input_text})

    sleep(2)

    begin = get2(azure_client, "開始", 0.43, 0.61)
    _click({"position": begin})
    sleep(2)

    shot = pg.screenshot()
    shot.save("./data/screenshots/save.png")
    text = gemini_reason.generate("この画面の内容を全てテキストに起こし,査定内容で確認できる情報をすべて取得して",
                                  image_path="./data/screenshots/save.png")
    text = re.search(r"<TEXT>(.*?)</TEXT>", text)

    if text is not None:
        text = text.group(1).strip()
        convert_text_file(manager, text)

