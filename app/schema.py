from pydantic import BaseModel
import typing as T


class DummyTask(BaseModel):
    prompt: str
    negative_prompt: str
    input_image_uuid: str