
import pytest
from fastapi.testclient import TestClient
from main import app  # Assuming the main FastAPI app is in main.py

client = TestClient(app)

def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {'Hello': 'World'}

# Add more tests for other functionalities as needed.
