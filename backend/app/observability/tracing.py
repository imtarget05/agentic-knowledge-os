from app.config import settings
from app.observability.logging import logger

class ObservabilityTracer:
    def __init__(self):
        self.langfuse_enabled = False
        self._init_langfuse()

    def _init_langfuse(self):
        if settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY:
            try:
                from langfuse import Langfuse
                self.langfuse_client = Langfuse(
                    public_key=settings.LANGFUSE_PUBLIC_KEY,
                    secret_key=settings.LANGFUSE_SECRET_KEY,
                    host=settings.LANGFUSE_HOST
                )
                self.langfuse_enabled = True
                logger.info("Langfuse observability tracking successfully enabled.")
            except Exception as e:
                logger.warning(f"Failed to initialize Langfuse SDK: {str(e)}")
        else:
            logger.info("Langfuse credentials missing. Running in standard structured log-trace mode.")

    def trace_agent_step(self, trace_id: str, agent_name: str, step_name: str, input_payload: str, output_payload: str):
        """
        Traces individual sub-agent nodes steps. Sends to Langfuse if configured, 
        otherwise writes to the JSON logs.
        """
        logger.info(
            f"Trace Step: [{step_name}] in Agent '{agent_name}' completed.",
            extra={
                "trace_id": trace_id,
                "agent_name": agent_name,
                "step_name": step_name,
                "extra_info": {
                    "input_length": len(input_payload),
                    "output_length": len(output_payload)
                }
            }
        )
        
        if self.langfuse_enabled:
            try:
                # Log step to Langfuse span
                trace = self.langfuse_client.trace(id=trace_id, name="agentic_knowledge_os_flow")
                trace.span(
                    name=step_name,
                    input=input_payload,
                    output=output_payload,
                    metadata={"agent": agent_name}
                )
            except Exception as e:
                logger.debug(f"Failed to send trace span to Langfuse: {str(e)}")

tracer = ObservabilityTracer()
