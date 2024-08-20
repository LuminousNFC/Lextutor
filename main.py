"""Module docstring"""
# Main FastAPI application setup
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    """Function docstring"""
    return {"Hello": "World"}
