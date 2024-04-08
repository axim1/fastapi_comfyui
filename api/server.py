from fastapi import FastAPI, BackgroundTasks, Depends
from api.router import router
from api.request import request_router

def create_app():
    app = FastAPI()
    app.include_router(router)
    app.include_router(request_router)
    app.redirect_slashes = False
    return app

app = create_app()
