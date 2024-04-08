from fastapi import (
    File, UploadFile, FastAPI, HTTPException, Form, Request, BackgroundTasks, Depends
    )
from app.service import StableDiffusionService
from uuid import uuid4
import os
import sys
import shutil
import requests
import time
import queue
import threading
import random
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from api.response import ProductWorkflowResponse
from api.bgfunctions import productworkflowbg
import typing as T
from api.request import read_image
# count of number of tasks running
global_counter = 0
router = InferringRouter()
from core.config import Settings
env = Settings()

def doStatusCheck():
    while True:
        # sending the callback of completed task to the server
        callback_payload = q.get()
        try:
            start_time = time.time()
            callback_data = callback_payload['callback_data']
            callback_url = callback_payload['callback_url']
            response = requests.post(callback_url, json=callback_data, tmiout=10)
            response.raise_for_status()
            print(f"Time taken to send the callback: {time.time() - start_time}")
        
        except Exception as e:
            print(f"Error in sending the callback: {e}")
        finally:
            q.task_done()

q = queue.Queue()
# starting the status check thread
status_check_thread = threading.Thread(target=doStatusCheck)
status_check_thread.start()



@cbv(router)
class StableDiffusion:
    svc: StableDiffusionService = Depends(StableDiffusionService)
    
    @router.get("/")
    def read_root(self):
        return {"Hello": "World"}

    
    @router.post('/dummyworkflow')
    async def dummyworkflow(
        self,
        prompt: str = Form(),
        negative_prompt: str = Form(default=""),
        input_image: UploadFile = File(...),
        num_images: int = Form(1, description="Number of images to generate"),
        revert_extra: str = Form(default=None, description= " Identifier to revert the extra data in the callback url"),
        callback_url: str = Form(default=None, description="Callback URL to send the generated images"),
        background_tasks: BackgroundTasks = BackgroundTasks()
        )->ProductWorkflowResponse:

        input_image = read_image(input_image)
        input_image_uuid = str(uuid4())
        input_image.save(f"{env.SAVE_DIR}/{input_image_uuid}.png")
        if revert_extra:
            revert_extra = str(uuid4())

        # generating multiple uuids and seeds for the images
        uuid_mul = [str(uuid4()) for i in range(num_images)]

        images_info = []
        for i in range(num_images):
            images_info.append({'image_uuid': str(uuid_mul[i])})
            
        # getting the input data from the request and passing it to background function
        background_tasks.add_task(productworkflowbg,
                                sd_svc=self.svc,
                                prompt=prompt,
                                negative_prompt=negative_prompt,
                                input_image_uuid=input_image_uuid,
                                num_images=num_images,
                                uuid_mul=uuid_mul,
                                revert_extra=revert_extra,
                                q=q,
                                callback_url=callback_url
                                )
        return ProductWorkflowResponse(
            prompt=prompt,
            negative_prompt=negative_prompt,
            num_images=num_images,
            images_info=images_info
        )

