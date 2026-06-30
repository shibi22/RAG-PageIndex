import asyncio
from typing import AsyncGenerator, Dict, Any

from agents import Agent, Runner, function_tool
from agents.stream_events import RawResponsesStreamEvent, RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent, ResponseReasoningSummaryTextDeltaEvent

from backend.services import document_service

AGENT_SYSTEM_PROMPT = """
You are PageIndex, a document QA assistant.
TOOL USE:
- Call get_document() first to confirm status and page/line count.
- Call get_document_structure() to identify relevant page ranges.
- Call get_page_content(pages="5-7") with tight ranges; never fetch the whole document.
- Before each tool call, output one short sentence explaining the reason.
Answer based only on tool output. Be concise.
"""

def create_agent_for_doc(doc_id: str) -> Agent:
    @function_tool
    def get_document() -> str:
        """Get document metadata: status, page count, name, and description."""
        return document_service.get_document_metadata(doc_id)

    @function_tool
    def get_document_structure() -> str:
        """Get the document's full tree structure (without text) to find relevant sections."""
        return document_service.get_document_structure(doc_id)

    @function_tool
    def get_page_content(pages: str) -> str:
        """
        Get the text content of specific pages or line numbers.
        Use tight ranges: e.g. '5-7' for pages 5 to 7, '3,8' for pages 3 and 8, '12' for page 12.
        """
        return document_service.get_page_content(doc_id, pages)

    return Agent(
        name="PageIndex_Agent",
        instructions=AGENT_SYSTEM_PROMPT,
        tools=[get_document, get_document_structure, get_page_content],
        model="gpt-4o-mini",
    )

async def stream_chat_events(doc_id: str, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Streams chat events for a specific document.
    Yields dictionaries with 'type' and 'data' keys suitable for SSE or API consumption.
    """
    if not document_service.check_doc_exists(doc_id):
        yield {"type": "error", "data": f"Document ID {doc_id} not found."}
        return

    agent = create_agent_for_doc(doc_id)
    streamed_run = Runner.run_streamed(agent, prompt)
    
    async for event in streamed_run.stream_events():
        if isinstance(event, RawResponsesStreamEvent):
            if isinstance(event.data, ResponseReasoningSummaryTextDeltaEvent):
                yield {"type": "reasoning", "delta": event.data.delta}
            elif isinstance(event.data, ResponseTextDeltaEvent):
                yield {"type": "text", "delta": event.data.delta}
        elif isinstance(event, RunItemStreamEvent):
            item = event.item
            if item.type == "tool_call_item":
                raw = item.raw_item
                args = getattr(raw, "arguments", "{}")
                yield {"type": "tool_call", "name": raw.name, "arguments": args}
            elif item.type == "tool_call_output_item":
                yield {"type": "tool_call_output", "output": str(item.output)}
