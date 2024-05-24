from pydantic import BaseModel

class ProductWorkflowResponse(BaseModel):
    prompt: str
    negative_prompt: str
    # cond_prompt:str
    num_images: int
    images_info: list

class VirtualTryonResponse(BaseModel):
    num_images: int
    category: str
    images_info: list