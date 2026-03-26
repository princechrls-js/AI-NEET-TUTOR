from fastapi.testclient import TestClient
import pytest
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_list_subjects():
    response = client.get("/subjects/")
    assert response.status_code == 200
    data = response.json()
    assert "available_subjects" in data
    assert "biology" in data["available_subjects"]
    assert "chemistry" in data["available_subjects"]
    assert "physics" in data["available_subjects"]
