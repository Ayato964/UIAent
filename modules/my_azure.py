import json
import os
import time
import requests
import pyautogui
from io import BytesIO
from PIL import Image


def get_client(url: str):
    """
    :param url: {"name": "<endpoint>", "token": "<key>"} の JSON ファイルパス
    :return: REST API 呼び出しに必要な情報をまとめた dict
    """
    with open(url, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {
        "endpoint": data["name"].rstrip("/"),  # e.g. https://<your-region>.api.cognitive.microsoft.com
        "key": data["token"]
    }


def capture_screenshot() -> BytesIO:
    """
    pyautogui でスクリーンショットを撮り、BytesIO を返す
    """
    screenshot = pyautogui.screenshot()
    buf = BytesIO()
    screenshot.save(buf, format="PNG")
    buf.seek(0)
    return buf


def find_text_position(client: dict, target: str):
    """
    REST Read API を使って OCR → 指定文字の中心座標を返す
    :param client: get_client() の返り値 dict
    :param target: 検出したい文字列
    :return: (x, y) または None
    """
    # 1) 画像データを取得
    buf = capture_screenshot()
    image_bytes = buf.getvalue()

    # 2) OCR リクエスト送信（非同期 API）
    ocr_url = f"{client['endpoint']}/vision/v3.2/read/analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": client["key"],
        "Content-Type": "application/octet-stream"
    }
    resp = requests.post(ocr_url, headers=headers, data=image_bytes)
    resp.raise_for_status()

    # 3) Operation-Location を取得
    operation_url = resp.headers["Operation-Location"]

    # 4) ポーリングして結果取得
    headers_get = {"Ocp-Apim-Subscription-Key": client["key"]}
    result = None
    for _ in range(20):
        r = requests.get(operation_url, headers=headers_get)
        r.raise_for_status()
        j = r.json()
        status = j.get("status")
        if status == "succeeded":
            result = j
            break
        if status == "failed":
            print("OCR 処理に失敗しました")
            return None
        time.sleep(0.5)
    if result is None:
        print("OCR 処理タイムアウト")
        return None

    # 5) JSON から座標を探す
    read_results = result["analyzeResult"]["readResults"]
    for page in read_results:
        for line in page.get("lines", []):
            # 行単位でまずマッチをチェック
            if target in line.get("text", ""):
                # 単語単位の bbox がある場合は先にそちらを探る
                for word in line.get("words", []):
                    if target in word.get("text", ""):
                        bbox = word["boundingBox"]
                        xs = bbox[0::2]; ys = bbox[1::2]
                        cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
                        print(f"[✓] '{word['text']}' at ({int(cx)}, {int(cy)})")
                        return int(cx), int(cy)
                # words がなければ行全体の bbox で返す
                bbox = line["boundingBox"]
                xs = bbox[0::2]; ys = bbox[1::2]
                cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
                print(f"[✓] '{line['text']}' at ({int(cx)}, {int(cy)})")
                return int(cx), int(cy)

    print(f"[✗] '{target}' not found.")
    return None


# 使用例
if __name__ == "__main__":
    time.sleep(3)  # 画面準備
    client = get_client("../config/azure.json")
    coords = find_text_position(client, "エラー")  # ←探したい文字列
    if coords:
        pyautogui.click(coords)
