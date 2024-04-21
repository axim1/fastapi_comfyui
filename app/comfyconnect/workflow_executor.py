from app.comfyconnect import ComfyConnector
from app.schema import DummyTask, VirtualTryonTask
import os
import logging
from core.config import Settings
env = Settings()
logger_main = logging.getLogger("logger_main")

class WorkflowExecutor(ComfyConnector):
    def __init__(self):
        super().__init__()
        self.workflow_mapping = {
            DummyTask: "dummy.json",
            VirtualTryonTask: "virtual_tryon.json",
        }
    def execute_workflow(self, task):
        task_dict = task.dict()
        payload = self.load_payload(f'workflows/{self.workflow_mapping[task.__class__]}')
        
        if isinstance(task, DummyTask):
            file_path = self.upload_image(os.path.join(env.SAVE_DIR, f"{task_dict['input_image_uuid']}.png"))
            # removing the file after uploading
            os.remove(os.path.join(env.SAVE_DIR, f"{task_dict['input_image_uuid']}.png"))
            images = self.dummyworkflow(payload, task_dict, file_path)

        elif isinstance(task, VirtualTryonTask):
            garment_file_path = self.upload_image(os.path.join(env.SAVE_DIR, f"{task_dict['garment_image_uuid']}.png"))
            model_file_path = self.upload_image(os.path.join(env.SAVE_DIR, f"{task_dict['model_image_uuid']}.png"))
            os.remove(os.path.join(env.SAVE_DIR, f"{task_dict['garment_image_uuid']}.png"))
            os.remove(os.path.join(env.SAVE_DIR, f"{task_dict['model_image_uuid']}.png"))
            images = self.virutal_tryon(payload, garment_file_path, model_file_path)
        else:
            image = [None]
            logger_main.info(f"Invalid Task Type")
        return images

    def dummyworkflow(
            self,
            payload,
            task_dict,
            file_path,
        ):
        try:
            ComfyConnector.replace_key_value_in_node(payload, target_key = "image", new_value = file_path['name'], target_title="Input Image")
            ComfyConnector.replace_key_value_in_node(payload, target_key = "text", new_value = task_dict['prompt'], target_title="Positive Prompt")
            ComfyConnector.replace_key_value_in_node(payload, target_key = "text", new_value = task_dict['negative_prompt'], target_title="Negative Prompt")
            images = self.generate_images(payload)
            return images
        except Exception as e:
            logger_main.exception(f"Error in generating image: {e}")
            return [None]
    
    def virutal_tryon(
            self,
            payload,
            garment_file_path: str,
            model_file_path: str,
            ):
        try:
            ComfyConnector.replace_key_value_in_node(payload, target_key = "image", new_value = garment_file_path['name'], target_title="Garment Image")
            ComfyConnector.replace_key_value_in_node(payload, target_key = "image", new_value = model_file_path['name'], target_title="Model Image")
            images = self.generate_images(payload)
            return images
        except Exception as e:
            logger_main.exception(f"Error in generating image: {e}")
            return [None]