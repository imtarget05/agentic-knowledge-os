from mcp.server.fastmcp import FastMCP
from app.config import settings
from app.observability.logging import logger

# Initialize FastMCP Server
mcp_server = FastMCP(
    name="Agentic Knowledge OS Server",
    version="1.0.0",
    description="Standardized MCP endpoints for retrieving technical documents, scanning repositories, and planning tasks"
)

# Dynamic registration helper to import tools, resources and prompts
def register_mcp_components():
    logger.info("Registering MCP tools, resources, and prompts...")
    try:
        import app.mcp_server.tools
        import app.mcp_server.resources
        import app.mcp_server.prompts
        logger.info("Successfully registered all MCP component modules.")
    except Exception as e:
        logger.error(f"Error registering MCP modules: {str(e)}", exc_info=True)

# Register components immediately
register_mcp_components()
