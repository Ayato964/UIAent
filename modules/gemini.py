

from google import genai
from google.genai import types


class GeminiClient:
    def __init__(self, api_key: str, model: str, prompt, is_ui_prompt: bool = False):
        self.client = genai.Client(api_key=api_key)
        self.model = model
        if is_ui_prompt:
            file = self.client.files.upload(file="./data/rag/prom.pdf")

        if is_ui_prompt:
            self.context = [
                types.Content(
                    role="user",
                    parts=[
                        #types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type),
                        types.Part.from_text(text=prompt),
                    ],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text="""承知いたしました。命令とスクリーンショットの画像をよく読み、ユーザーの指示に沿った指示とUI操作をエージェントに出力します。
                                        """),
                    ],
                ),
            ]
        else:
            self.context = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
                types.Content(
                    role="model",
                    parts=[
                        types.Part.from_text(text="""
                        承知いたしました。命令の内容とスクリーンショットの画像をよく読み、ユーザーの指示に沿った指示とUI操作をエージェントに出力します。
                        """),
                    ],
                ),
            ]


    def generate(self, input_text: str, image_path: str = None, gen_config=None, is_save_context=True):
        self.set_context(input_text, image_path=image_path, to="user")

        if gen_config is None:
            generate_content_config = types.GenerateContentConfig(
                response_mime_type="text/plain",
                temperature=0.5
            )
        else:
            generate_content_config = gen_config

        text = ""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
        contents=self.context,
        config=generate_content_config):
            chunk_text = chunk.text
            if chunk_text is not None and chunk_text != "None":
                text += chunk_text
            print(chunk_text, end="")

        if is_save_context:
           self.set_context(text, image_path=image_path, to="model")
        else:
            self.context = self.context[:-1]

        return text

    def set_context(self, input_text, image_path: str, to:str = "user"):
        if image_path is None:
            self.context.append(types.Content(
                role=to,
                parts=[
                    types.Part.from_text(text=input_text),
                ],
            ))
        else:
            file = self.client.files.upload(file=image_path)
            self.context.append(types.Content(
                role=to,
                parts=[
                    types.Part.from_uri(file_uri=file.uri, mime_type=file.mime_type),
                    types.Part.from_text(text=input_text),
                ],
            ))

