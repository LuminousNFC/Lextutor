"""Module docstring"""
# Main FastAPI application setup
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
    """Function docstring"""
def read_root():
    return {"Hello": "World"}
