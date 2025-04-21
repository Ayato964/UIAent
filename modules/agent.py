import json
import re
from time import sleep
from .my_azure import find_text_position
import pyautogui as pg

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
        # Perform type action
        pass
    elif action_type == "position":
        # Move mouse to specified position
        pass
    else:
        print("Unknown action type")
    print("処理が完了しました。")


def text_to_json(text, act: str):
    """
    Convert text to JSON format.
    """
    act_json = dict()
    act_json["action"] = act
    act_json["position"] = text
    return act_json

def thinking(input_text: str, gemini_reason, azure_client):
    count = 0
    is_thinking = True
    while is_thinking:
        screenshot = pg.screenshot()
        path = f"data/screenshots/sc_{count}.png"
        screenshot.save(path)
        sleep(1)
        prompt = gemini_reason.generate(input_text=input_text, image_path=path)
        act = re.search(r"<Action>(.*?)</Action>", prompt, re.DOTALL)
        act = act.group(1).strip()
        prompt = re.search(r"<Prompt>(.*?)</Prompt>", prompt, re.DOTALL).group(1).strip()

        feedback = find_text_position(azure_client, prompt)
        print(feedback)

        js = text_to_json(feedback, act)
        print(f"FeedBack: {js}")
        action(js)
        count += 1
        input_text = "Next Action"
        sleep(1)
