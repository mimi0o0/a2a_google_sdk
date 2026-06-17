"""Orchestrator main brain that dervies multi agent pipeline
   what is does:
   -accept a writing topic 
   -discover each agent by fetching their agent card
   -calls agent in sequence 
   -pass output of each agent as the INPUT to the next
   -saves the final article and seo data to disk
       """

import httpx
import asyncio
import sys
from datetime import datetime
import uuid
from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (SendMessageRequest, MessageSendParams, Message,Task,
                       Part, TextPart, Role, TaskState)
#from core.config import settings
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AGENT_URLS = {
    "outline": "http://localhost:8001",
    "writer": "http://localhost:8002",
    "editor": "http://localhost:8003",
    "seo": "http://localhost:8004"
}


async def send_to_agent(
        agent_name: str,
        agent_base_url: str,
        user_message: str,
        httpx_client: httpx.AsyncClient
) -> str:
    """Discovers an A2A agent, send it a message, and return its text response"""

    print(f"\n  → Calling [{agent_name}]")
    
    """1> Discover the agent capabilities via its agent card"""
    resolver = A2ACardResolver(
        httpx_client=httpx_client,
        base_url=agent_base_url
    )
    agent_card = await resolver.get_agent_card()
    print(f"     Discovered: {agent_card.name}")
    print(f"     Skills: {[s.id for s in agent_card.skills]}")

    """2> Create the A2A client for this agent"""
    client = A2AClient(
        httpx_client=httpx_client,
        agent_card=agent_card
    )

    """3> Build the request payload"""
    message = Message(
        messageId=str(uuid.uuid4()),
        role=Role.user,
        parts=[
            Part(root=TextPart(text=user_message))
        ],
    )
    request = SendMessageRequest(
        id=str(uuid.uuid4()),
        params=MessageSendParams(message=message),
    )
    
    print(f"     Sending message ({len(user_message)} chars)...")
    
    """ERROR FIX 1: send_message not send.message"""
    response = await client.send_message(request)

    """Response is a SendMessageResponse"""
    result = response.root
    
    if hasattr(result, "error"):
        raise RuntimeError(
            f"A2A RPC error from {agent_name}: {result.error}"
        )

    result_obj = result.result

    if isinstance(result_obj, Message):

        text_parts = [
            p.root.text
            for p in result_obj.parts
            if hasattr(p.root, "text")
        ]
        agent_response = "\n".join(text_parts)

    elif isinstance(result_obj, Task):
        if result_obj.status.state == TaskState.failed:
            raise RuntimeError(
                f"Agent[{agent_name}] returned failed status. "
                f"Message: {result_obj.status.message}"
            )
        if result_obj.status.state not in (TaskState.completed, TaskState.submitted):
            print(f"     WARNING: unexpected state={result_obj.status.state}")

        text_parts = [
            p.root.text
            for p in result_obj.status.message.parts
            if hasattr(p.root, "text")
        ]
        agent_response = "\n".join(text_parts)

    else:
        raise RuntimeError(f"Unexpected result type from {agent_name}: {type(result_obj)}")
    print(f"     ✓ Got response ({len(agent_response)} chars)")
    return agent_response


async def run_writing_pipeline(topic: str) -> None:
    """Orchestrates the full writing pipeline:
    topic -> outline -> article draft -> edited article -> SEO metadata
    
    We use one shared httpx.AsyncClient for all agent calls"""

    print("\n" + "="*80)
    print("  WRITING PIPELINE")
    print(f"  Topic: {topic}")
    print(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("="*80)

    async with httpx.AsyncClient(timeout=120.0) as http:
        
        """STAGE 1: Create outline"""
        print("\n[STAGE 1] Creating outline...")
        outline = await send_to_agent(
            agent_name="Outline Agent",
            agent_base_url=AGENT_URLS["outline"],
            user_message=topic,
            httpx_client=http,
        )
        print(f"\n--- OUTLINE PREVIEW ---")
        print(outline[:300] + "...")

        """STAGE 2: Write full article"""
        print("\n[STAGE 2] Writing full article...")
        """ERROR FIX 4: Use correct AGENT_URLS key and pass user_message"""
        draft = await send_to_agent(
            agent_name="Writer Agent",
            agent_base_url=AGENT_URLS["writer"],
            user_message=f"Write a full article based on this outline:\n\n{outline}",
            httpx_client=http,
        )
        print(f"\n--- DRAFT PREVIEW ---")
        print(draft[:300] + "...")

        """STAGE 3: Edit and polish"""
        print("\n[STAGE 3] Editing and polishing...")
        polished = await send_to_agent(
            agent_name="Editor Agent",
            agent_base_url=AGENT_URLS["editor"],
            user_message=f"Edit and polish this article draft:\n\n{draft}",
            httpx_client=http,
        )

        """STAGE 4: Generate SEO metadata"""
        print("\n[STAGE 4] Generating SEO metadata...")
        seo_data = await send_to_agent(
            agent_name="SEO Agent",
            agent_base_url=AGENT_URLS["seo"],
            user_message=f"Generate SEO metadata for this article:\n\n{polished}",
            httpx_client=http,
        )

        """Save outputs to files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_topic = topic[:40].replace(" ", "_").replace("/", "-")
        article_path = f"output_{safe_topic}_{timestamp}.md"
        seo_path = f"output_seo_{safe_topic}_{timestamp}.txt"

        with open(article_path, "w", encoding="utf-8") as f:
            f.write(f"# {topic}\n\n")
            f.write("---\n*Pipeline stages: Outline → Writer → Editor → SEO*\n---\n\n")
            f.write(polished)

        with open(seo_path, "w", encoding="utf-8") as f:
            f.write(f"SEO Metadata for: {topic}\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n\n")
            f.write(seo_data)

        """Print final results"""
        print("\n" + "="*80)
        print("  PIPELINE COMPLETE ✓")
        print("="*80)
        print(f"\n  Article saved to : {article_path}")
        print(f"  SEO data saved to: {seo_path}")
        print(f"\n  Article length   : {len(polished)} characters")
        print(f"\n--- FINAL ARTICLE ---\n")
        print(polished[:2000])
        if len(polished) > 2000:
            print(f"\n[... {len(polished)-2000} more characters in file ...]")
        print(f"\n--- SEO METADATA ---\n")
        print(seo_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python client/orchestrator.py \"Your writing topic here\"")
        print("Example: python client/orchestrator.py \"The future of renewable energy\"")
        sys.exit(1)
    
  
    topic = " ".join(sys.argv[1:])
    asyncio.run(run_writing_pipeline(topic))