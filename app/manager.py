from service_streamer import ThreadedStreamer
from fastapi import Depends
from functools import lru_cache
from app.comfyconnect import ComfyConnector, WorkflowExecutor
from app.schema import DummyTask
from core.config import Settings
import logging
import os
env = Settings()
logger_main = logging.getLogger("logger_main")

class APIManager(WorkflowExecutor):
    def __init__(self):
        super().__init__()
             
    
    def predict(self, task):
        task_new = task[0]
        try:
            images = self.execute_workflow(task_new)
        except Exception as e:
            logger_main.exception(f"Error in generating image: {e}")
            images = [None]
        logger_main.info(f"Predicting data: {task_new.dict()}")
        return images
        
    
@lru_cache(maxsize=1)
def build_streamer()->ThreadedStreamer:
    manager = APIManager()
    streamer = ThreadedStreamer(
        manager.predict,
        batch_size=1,
        max_latency=0.1,
        )
    return streamer, manager



