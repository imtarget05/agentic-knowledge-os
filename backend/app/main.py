import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.observability.logging import logger
from app.api import ingest, chat, eval, agents

app = FastAPI(
    title=settings.APP_NAME,
    description="MCP-powered Multi-Agent RAG Knowledge Operating System",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None
)

# Set up CORS middleware for frontend API access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware for Trace ID injection and Timing logs
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    trace_id = request.headers.get("X-Trace-ID", f"tr-{uuid.uuid4().hex[:8]}")
    request.state.trace_id = trace_id
    
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    duration = time.time() - start_time
    response.headers["X-Trace-ID"] = trace_id
    
    logger.info(
        f"API Request: {request.method} {request.url.path} Completed in {duration:.4f}s with status {response.status_code}",
        extra={"trace_id": trace_id}
    )
    
    return response

# Register API Routers
app.include_router(ingest.router)
app.include_router(chat.router)
app.include_router(eval.router)
app.include_router(agents.router)

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "primary_llm": settings.PRIMARY_LLM_PROVIDER,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "qdrant_mode": settings.QDRANT_MODE
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
