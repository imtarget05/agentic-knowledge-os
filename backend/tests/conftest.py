import pytest
import os
import sys

# Add backend root folder to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Force mock environment settings for testing
os.environ["PRIMARY_LLM_PROVIDER"] = "mock"
os.environ["EMBEDDING_PROVIDER"] = "local"
os.environ["QDRANT_MODE"] = "local"
os.environ["SQLITE_DB_PATH"] = "data/processed/test_tasks.db"

from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture(scope="session")
def client():
    """Reusable session-scoped test client"""
    with TestClient(app) as c:
        yield c

@pytest.fixture(autouse=True)
def clean_test_env():
    """Ensure clean test task database before each test"""
    db_path = os.environ["SQLITE_DB_PATH"]
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
    yield
    if os.path.exists(db_path):
        try:
            os.remove(db_path)
        except Exception:
            pass
