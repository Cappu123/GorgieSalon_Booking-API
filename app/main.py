"""Import all the necessary libraries and modules"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.server_side import admin, stylist
from . import models
from .database import engine
from .server_side import user, authentication
from pydantic_settings import BaseSettings
from .configuration import settings

models.Base.metadata.create_all(bind=engine)

app = FastAPI()


app.include_router(user.router)
app.include_router(stylist.router)
app.include_router(authentication.router)
app.include_router(admin.router)



@app.get("/")
def homePage():

    return {"Hello": "Welcome to Gorgies"}

