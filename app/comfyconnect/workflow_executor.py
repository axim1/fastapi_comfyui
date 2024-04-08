from app.comfyconnect import ComfyConnector
from app.schema import DummyTask
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
            "sketch2image": "product_workflow.json",
        }
    def execute_workflow(self, task):
        task_dict = task.dict()
        payload = self.load_payload(f'workflows/{self.workflow_mapping[task.__class__]}')
        file_path = self.upload_image(os.path.join(env.SAVE_DIR, f"{task_dict['input_image_uuid']}.png"))
        # removing the file after uploading
        os.remove(os.path.join(env.SAVE_DIR, f"{task_dict['input_image_uuid']}.png"))
        if isinstance(task, DummyTask):
           images = self.dummyworkflow(payload, task_dict, file_path)
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