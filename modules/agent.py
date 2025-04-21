import json
import re
from time import sleep

import pyautogui as pg

def _duble_click(target: dict):
    """
    中点を求める
    :param target:
    :return:
    """
    ymin, xmin, ymax, xmax = target["box_2d"]
    ymin *= 1.07
    xmin *= 1.92
    ymax *= 1.07
    xmax *= 1.92
    center_x = xmin + (xmax - xmin) / 2
    center_y = ymin + (ymax - ymin) / 2

    _move({"position":[center_x, center_y]})

    print("マウスにダブルクリックさせています。。。。")
    pg.doubleClick( button="left")

def _click(target: dict):
    """
    中点を求める
    :param target:
    :return:
    """
    ymin, xmin, ymax, xmax = target["box_2d"]
    ymin *= 1.07
    xmin *= 1.92
    ymax *= 1.07
    xmax *= 1.92
    center_x = xmin + (xmax - xmin) / 2
    center_y = ymin + (ymax - ymin) / 2

    _move({"position":[center_x, center_y]})
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


def text_to_json(text: str, act: str):
    """
    Convert text to JSON format.
    """
    match = re.search(r"```json(.*?)```", text, re.DOTALL)
    if match:
        js_str = match.group(1).strip()  # JSON部分の文字列
        # 2. JSONに変換
        data = json.loads(js_str)
        data[0]["action"] = act
        return data[0]
    else:
        assert "JSONが見つかりませんでした。"
        return None


def thinking(input_text: str, gemini_reason, gemini_json):
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
        print(f"Prompt: {prompt}")


        feedback = gemini_json.generate(input_text=f"""
        Detect {prompt}. 
        Output a json list where each entry contains the 2D bounding box in "box_2d" and a text label in "label".
        """, image_path=path)

        js = text_to_json(feedback, act)
        print(f"FeedBack: {js}")
        action(js)
        count += 1
        input_text = "Next Action"
        sleep(1)
