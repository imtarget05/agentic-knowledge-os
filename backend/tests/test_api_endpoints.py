import pytest
import json

def test_health_check(client):
    """Verify that health check endpoint returns 200 OK and valid status"""
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_api_agents_decompose(client):
    """Verify that decompose endpoint successfully constructs and returns JSON execution plans"""
    payload = {
        "request": "Rà soát bảo mật mã nguồn và đề xuất cập nhật hạ tầng k3s",
        "max_workers": 4,
        "enable_optimization": True
      }
    response = client.post("/api/agents/decompose", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "request_id" in data
    assert data["total_subtasks"] >= 4
    assert len(data["parallel_groups"]) >= 4
    assert len(data["subtasks"]) >= 4

def test_api_agents_execute_stream(client):
    """Verify that execute streaming endpoint streams NDJSON updates with custom headers"""
    payload = {
        "request": "Phân tích cấu trúc codebase",
        "max_workers": 4,
        "enable_optimization": True
    }
    
    response = client.post("/api/agents/execute", json=payload)
    
    assert response.status_code == 200
    assert "application/x-ndjson" in response.headers["content-type"]
    
    # Read streamed lines
    lines = [line.decode("utf-8") for line in response.iter_lines() if line]
    assert len(lines) >= 3
    
    # First chunk should indicate decomposition is complete
    first_chunk = json.loads(lines[0])
    assert first_chunk["phase"] == "decomposition_complete"
    assert "decomposition" in first_chunk
    
    # Last chunk should indicate execution complete
    last_chunk = json.loads(lines[-1])
    assert last_chunk["phase"] == "execution_complete"
    assert "metrics" in last_chunk
    assert last_chunk["status"] == "completed"
