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

def get(client: dict, target: str, sw: float, sh: float):
    """
    REST Read API を使って OCR → 指定文字の中心座標を返す
    :param client: get_client() の返り値 dict
    :param target: 検出したい文字列
    :param sw: スクリーンショット画像の幅に対する相対座標 (0.0 - 1.0)
    :param sh: スクリーンショット画像の高さに対する相対座標 (0.0 - 1.0)
    :return: (x, y) または None
    """
    # 1) 画像データを取得
    buf = capture_screenshot()
    image = Image.open(buf)
    image_width, image_height = image.size

    absolute_x = int(image_width * sw)
    absolute_y = int(image_height * sh)

    # 2) OCRリクエスト送信
    ocr_url = f"{client['endpoint']}/vision/v3.2/read/analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": client["key"],
        "Content-Type": "application/octet-stream"
    }
    resp = requests.post(ocr_url, headers=headers, data=buf.getvalue())
    resp.raise_for_status()

    # 3) Operation-Location取得
    operation_url = resp.headers["Operation-Location"]

    # 4) ポーリングで結果取得
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

    # 5) すべての単語を優先的に探す
    closest_text = None
    closest_distance = float("inf")
    closest_coords = None
    fallback_candidates = []

    read_results = result["analyzeResult"]["readResults"]
    for page in read_results:
        for line in page.get("lines", []):
            # まず単語を全部チェック
            for word in line.get("words", []):
                if target in word.get("text", ""):
                    bbox = word["boundingBox"]
                    xs = bbox[0::2]; ys = bbox[1::2]
                    cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
                    distance = ((cx - absolute_x) ** 2 + (cy - absolute_y) ** 2) ** 0.5
                    if distance < closest_distance:
                        closest_distance = distance
                        closest_text = word["text"]
                        closest_coords = [int(cx), int(cy)]
            # fallback用に、行単位も記録しておく
            if target in line.get("text", ""):
                fallback_candidates.append(line)

    # 単語レベルで見つかればそれを返す
    if closest_coords:
        print(f"[✓] 最も近い単語: '{closest_text}' at {closest_coords}")
        return closest_coords
    print("単語では見つからないね。")
    # fallback: 単語で見つからなかったときだけ行単位で探す
    closest_distance = float("inf")
    for line in fallback_candidates:
        bbox = line["boundingBox"]
        xs = bbox[0::2]; ys = bbox[1::2]
        cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
        distance = ((cx - absolute_x) ** 2 + (cy - absolute_y) ** 2) ** 0.5
        if distance < closest_distance:
            closest_distance = distance
            closest_text = line["text"]
            closest_coords = [int(cx), int(cy)]

    if closest_coords:
        print(f"[✓] 最も近い行: '{closest_text}' at {closest_coords}")
        return closest_coords

    print(f"[✗] '{target}' に近い文字列が見つかりませんでした。")
    return None


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
                        return [int(cx), int(cy)]
                # words がなければ行全体の bbox で返す
                bbox = line["boundingBox"]
                xs = bbox[0::2]; ys = bbox[1::2]
                cx = sum(xs) / len(xs); cy = sum(ys) / len(ys)
                print(f"[✓] '{line['text']}' at ({int(cx)}, {int(cy)})")
                return [int(cx), int(cy)]

    print(f"[✗] '{target}' not found.")
    return None

def get2(client: dict, target: str, sw: float, sh: float):
    """
    REST Read API を使って OCR → 指定文字列に対応する単語列の中心座標を返す
    :param client: get_client() の返り値 dict
    :param target: 検出したい文字列
    :param sw: スクリーンショット画像の幅に対する相対座標 (0.0 - 1.0)
    :param sh: スクリーンショット画像の高さに対する相対座標 (0.0 - 1.0)
    :return: (x, y) または None
    """
    # 1) 画像データを取得
    buf = capture_screenshot()
    image = Image.open(buf)
    image_width, image_height = image.size

    absolute_x = int(image_width * sw)
    absolute_y = int(image_height * sh)

    # 2) OCRリクエスト送信
    ocr_url = f"{client['endpoint']}/vision/v3.2/read/analyze"
    headers = {
        "Ocp-Apim-Subscription-Key": client["key"],
        "Content-Type": "application/octet-stream"
    }
    resp = requests.post(ocr_url, headers=headers, data=buf.getvalue())
    resp.raise_for_status()

    # 3) Operation-Location取得
    operation_url = resp.headers["Operation-Location"]

    # 4) ポーリングで結果取得
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

    # 5) 単語を収集
    read_results = result["analyzeResult"]["readResults"]
    all_words = []

    for page in read_results:
        for line in page.get("lines", []):
            for word in line.get("words", []):
                bbox = word.get("boundingBox", [])
                if not bbox:
                    continue
                xs = bbox[0::2]
                ys = bbox[1::2]
                cx = sum(xs) / len(xs)
                cy = sum(ys) / len(ys)
                all_words.append({
                    "text": word.get("text", ""),
                    "center": (int(cx), int(cy))
                })

    # 6) 単語を全部連結して、targetを探す
    concatenated = ""
    positions = []
    indices = []

    for idx, word in enumerate(all_words):
        concatenated += word["text"]
        positions.append(word["center"])
        indices.append(idx)

    if target not in concatenated:
        print(f"[✗] '{target}' に一致する連結テキストが見つかりませんでした。")
        return None

    # 7) どこにマッチしたかを特定する
    match_start = concatenated.find(target)
    match_end = match_start + len(target)

    # 単語リストのどの範囲にまたがるかを特定
    char_count = 0
    matched_indices = []
    for idx, word in enumerate(all_words):
        word_len = len(word["text"])
        next_char_count = char_count + word_len
        if (char_count < match_end and next_char_count > match_start):
            matched_indices.append(idx)
        char_count = next_char_count

    if not matched_indices:
        print(f"[✗] '{target}' の対応単語が見つかりませんでした。")
        return None

    # 8) マッチした単語たちの座標を平均する
    matched_centers = [all_words[i]["center"] for i in matched_indices]
    avg_x = int(sum(c[0] for c in matched_centers) / len(matched_centers))
    avg_y = int(sum(c[1] for c in matched_centers) / len(matched_centers))

    print(f"[✓] '{target}' を検出 中心座標: ({avg_x}, {avg_y})")
    return [avg_x, avg_y]

# 使用例
if __name__ == "__main__":
    time.sleep(3)  # 画面準備
    client = get_client("../config/azure.json")
    coords = find_text_position(client, "エラー")  # ←探したい文字列
    if coords:
        pyautogui.click(coords)
