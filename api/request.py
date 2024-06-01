import time
from fastapi import UploadFile,BackgroundTasks
from PIL import Image, ImageOps
import os
import json
import cv2
import base64
from fastapi.responses import StreamingResponse
import io
from fastapi_utils.inferring_router import InferringRouter
from fastapi_utils.cbv import cbv


request_router = InferringRouter()

def read_image(image: UploadFile) -> Image.Image:

    image = Image.open(image.file)
    image = ImageOps.exif_transpose(image)
    image = image.convert("RGB")
    return image

def delete_image_after_delay(image_path: str, delay: int = 3600):
    time.sleep(delay)
    if os.path.exists(image_path):
        os.remove(image_path)
        print("Image deleted")
@cbv(request_router)
class StatusEndpoint:

    @request_router.get("/getimage/{image_uuid}")
    async def get_image(self, image_uuid: str, delete: bool = True, type: str = "PNG", base64_c: bool = False, quality_level: int = 90, background_tasks: BackgroundTasks = BackgroundTasks()):
        # Validate quality_level and type
        if not 0 <= quality_level <= 100:
            quality_level = 90
        if type not in ['PNG', 'JPEG', 'WebP', 'GIF']:
            return "Unsupported image type"

        image_path = f'./static/{image_uuid}.png'
        
        # Check if the file exists
        if not os.path.exists(image_path) or not image_uuid:
            return {"status": "started - processing"}

        # Read the image from disk
        image = cv2.imread(image_path)

        # Handle JSON type separately
        if type == 'JSON':
            cv2_image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return json.dumps(cv2_image_rgb.tolist())

        # Encode the image according to the requested type
        _, buffer = cv2.imencode(f'.{type.lower()}', image)
        encoded_image = buffer.tobytes()

        if delete:
            os.remove(image_path)
        else:
            # Schedule the background task to delete the image after an hour
            print("Background process to delete image after 1 hour initiated")
            background_tasks.add_task(delete_image_after_delay, image_path)


        if base64_c:
            encoded_image_string = base64.b64encode(encoded_image).decode()
            payload = {
                "image_mime_type": f"image/{type}",
                "image_data": encoded_image_string,
                "image_uuid": image_uuid
            }
            return payload

        return StreamingResponse(io.BytesIO(encoded_image), media_type=f"image/{type}")