import asyncio
from backend.services.document_service import index_document
from backend.services.chat_service import stream_chat_events

def test_index():
    return index_document("Preparing-for-an-Interview.pdf")

async def test_chat(doc_id):
    print(f"\n--- Chat Stream for {doc_id} ---")
    async for event in stream_chat_events(doc_id, "What does it say about dress for success?"):
        print(event)

if __name__ == "__main__":
    doc_id = test_index()
    asyncio.run(test_chat(doc_id))
