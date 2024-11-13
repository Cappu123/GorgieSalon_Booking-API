"""Import all the necessary libraries and modules"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.server_side import admin, stylist, booking, service
from . import models
from .database import engine
from .server_side import user, authentication, review
from pydantic_settings import BaseSettings
from .configuration import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],

)

app.include_router(user.router)
app.include_router(stylist.router)
app.include_router(authentication.router)
app.include_router(admin.router)
app.include_router(booking.router)
app.include_router(service.router)
app.include_router(review.router)



@app.get("/")
def homePage():

    return {"Hello": "Welcome to Gorgies"}


