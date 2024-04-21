from service_streamer import ThreadedStreamer
from app.manager import APIManager, build_streamer
from fastapi import Depends
from PIL import Image
from app.schema import DummyTask, VirtualTryonTask
import typing as T

class StableDiffusionService:
    def __init__(self,
               streamer_in: ThreadedStreamer = Depends(build_streamer)
                ):
        self.streamer = streamer_in[0]
        self.manager = streamer_in[1]

    def text2img(self, text: str):
        task = [
            text
        ]
        self.summit(task)
    
    def dummyworkflow(
            self,
            prompt: str,
            negative_prompt: str,
            input_image_uuid: str,
            ):
        task = [
            DummyTask(
                prompt=prompt,
                negative_prompt=negative_prompt,
                input_image_uuid=input_image_uuid,
            )
        ]
        result = self.summit(task)
        if result:
            return result
        else:
            return None
        
    def virutal_tryon(
            self,
            garment_image_uuid: str,
            model_image_uuid: str,
            ):
        task = [
            VirtualTryonTask(
                garment_image_uuid=garment_image_uuid,
                model_image_uuid=model_image_uuid,
            )
        ]
        result = self.summit(task)
        if result:
            return result
        else:
            return None



    def summit(self, text: str):
        future = self.streamer.submit(text)
        try:
            result = future.result(timeout = 2000)
            if result[0]:
                return result[0]
            else:
                return None
        except Exception as e:
            print(f"Error in getting the result: {e}")
            return 
