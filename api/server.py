from fastapi import FastAPI, BackgroundTasks, Depends
from api.router import router
from api.request import request_router
from fastapi.middleware.cors import CORSMiddleware

def create_app():
    app = FastAPI()
    app.include_router(router)
    app.include_router(request_router)
    app.redirect_slashes = False
    # Allow requests from all origins
    app.add_middleware(
        CORSMiddleware,
    allow_origins=["*"],  # This should be restricted to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
    return app

app = create_app()
