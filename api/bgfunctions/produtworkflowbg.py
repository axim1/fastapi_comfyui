from .threadLock import thread_lock, global_counter
from core.config import Settings
env = Settings()
import logging
logger_main = logging.getLogger("logger_main")


def productworkflowbg(
        sd_svc,
        prompt,
        negative_prompt,
        input_image_uuid,
        num_images,
        uuid_mul,
        revert_extra,
        q,
        callback_url
    ):

    global global_counter
    with thread_lock:
        global_counter += 1
    try:
        for i in range(num_images):
            image = sd_svc.dummyworkflow(
                prompt=prompt,
                negative_prompt=negative_prompt,
                input_image_uuid=input_image_uuid,
                )
            if image:
                image.save(f'./static/{uuid_mul[i]}.png')
                logger_main.info(f"Image saved for {uuid_mul[i]}")
                if callback_url:
                    callback_data = {
                        "uuid": uuid_mul[i],
                        "revert_extra": f"{revert_extra}"
                    }
                    payload = {
                        "callback_url": f"{callback_url}",
                        "callback_data": callback_data
                    }
                    q.put(payload)
            else:
                logger_main.info(f"Image not saved for {uuid_mul[i]}")
            
    except Exception as e:
        logger_main.exception(f"Error in generating image: {e}")
    

    with thread_lock:
        global_counter -= 1