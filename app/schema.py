from pydantic import BaseModel
import typing as T


class DummyTask(BaseModel):
    prompt: str
    negative_prompt: str
    input_image_uuid: str

class VirtualTryonTask(BaseModel):
    model_image_uuid: str
    garment_image_uuid: str
