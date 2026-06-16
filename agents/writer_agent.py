"""writer agent runs on port 8002

WHAT IT DOES:
  Receives an outline (from the Outline Agent) and expands it into a full,
  well-written article with proper prose for each section.
  """
import uvicorn 
from a2a.types import (
    AgentCard,
    AgentSkill,
    AgentCapabilities,
    AgentAuthentication,

)
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handler import DefaultRequestHandler
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.event import EvenetQueue
from a2a.server.tasks import InMemoryTaskStore
from a2a.utils import new_agent_text_message
from llm.gemini_client import call_gemini
from a2a.server.events import EventQueue
import asyncio

port = 8002
writer_skill = AgentSkill(
    id="write_article",
    name="write full article",
    description=("Takes a structured outlinr and expands it into a complete,"
                 "well written article with an engaging introduction,detailed body"
                 "section, and strong conclusion"
    ),
    tags=["writing","article","content"],
    example=["Expand this outline into full article....",
             "Wriye an article based on this structure..."],
    inputModes=["text/plain"],
    outputModes=["text/plain"],

    )
writer_agent_card =AgentCard(
    name="Writer Agent",
    description= "Expands outlines into complete , well=written articles",
    url=f"http://localhost:{port}/",
    version="1.0.0",
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False),
    authentication=AgentAuthentication(schemas=["public"]),
    skills=[writer_skill],
)


class WriterAgentExecutor(AgentExecutor):
    """Takes an outline and calls gemini to write full article"""

    async def execute(
            self,
            context:RequestContext,
            event_queue:EvenetQueue,
    )->None:
        outline = context.get_user_input()

        prompt=f""""You are an expert content writer.
Below is an article outline. Write a complete, engaging article based on it.
 
OUTLINE:
{outline}
 
WRITING GUIDELINES:
- Write in a clear, engaging, authoritative voice
- Each section should be 2-3 paragraphs
- Use smooth transitions between sections
- Include specific examples or data where the outline suggests it
- The introduction should hook the reader in the first sentence
- The conclusion should leave the reader with a clear takeaway
- Total article length: ~800-1000 words
 
Output ONLY the full article text. No meta-commentary. """

        article_text =await asyncio.to_thread(call_gemini,prompt)
        event_queue.enqueue_event(new_agent_text_message(article_text))


    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise NotImplementedError("writer agent does not support cancellation")


def build_app():
    return A2AStarletteApplication(
        agent_card=writer_agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=WriterAgentExecutor(),
            task_store=InMemoryTaskStore()
        ),

    ).build()

if __name__ == "__main__":
    print(f"[WriterAgent] Starting on http://localhost:{port}")
    print(f"[WriterAgent] Agent Card: http://localhost:{port}/.well-known/agent.json")
    uvicorn.run(build_app(), host="0.0.0.0", port=port)