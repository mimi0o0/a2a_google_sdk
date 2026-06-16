"""editor agent runs on port 8003
WHAT IT DOES:
  Receives the raw article draft (from the Writer Agent) and returns a polished
  version: fixing grammar, improving sentence flow, tightening prose, and
  ensuring consistent tone."""

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

port=8003

editor_skill = AgentSkill(
    id="edit_article",
    name="edit and polish article",
    description=(
        "Reviews a draft article and returns an imporved version with"
        "corrected grammar, better sentence flow ,consistance tone and "
        "stronger word choices. Does NOT chnage the factual content"
    ),
    tags=["editing","proofreading","grammar","style","polish"],
    examples=["Edit this article draft :...",
            "proofread and improve this text:..."  
              
            ],
            inputModes=["text/plain"],
            outputModes=["text/plain"],
)

editor_agent_card=AgentCard(
    name="Editor Agent",
    description="polishes and imporve article draft for grammer ,style and flow",    url=f"http://localhost:{port}/",
    version="1.0.0",
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
    capabilitgies=AgentCapabilities(streaming=True),
    authetication=AgentAuthentication(schemes=["public"]),
    skills=[editor_skill],
)

class EditorAgentExecutor(AgentExecutor):
    """Polishes a draft article """

    async def execute(
            self,
            context:RequestContext,
            event_queue:EventQueue,
    )->None:
        draft=context.get_user_input()
        prompt=f"""You are a professional editor at a top publishing house.
Your job is to edit the following article draft for:
1. Grammar and spelling errors
2. Sentence flow and readability
3. Word choice — prefer strong, specific words over vague ones
4. Consistent tone (professional but approachable)
5. Paragraph transitions
 
DRAFT ARTICLE:
{draft}
 
EDITING RULES:
- Preserve ALL factual content and the article's structure
- Do NOT add new information or sections
- Do NOT change the main message or argument
- Fix passive voice where it weakens the writing
- Vary sentence length for rhythm
- Return the COMPLETE edited article only — no comments or markup"""
        edited_text=await asyncio.to_thread(call_gemini,prompt)
        event_queue.enqueue_event(new_agent_text_message(edited_text))
    

    async def cancel(self,context:RequestContext,event_queue:EvenetQueue)->None:
        raise NotImplementedError("editor agent does not support cancellation")
    

def build_app():
    return A2AStarletteApplication(
        agent_card=editor_agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=EditorAgentExecutor(),
            task_store=InMemoryTaskStore(),

        ),
    ).build()


if __name__ == "__main__":
    print(f"Editor Agent on http://localhost:{port}")
    print(f"editor agent card :http://localhost:{port}/.well-known/agent.json")
    uvicorn.run(build_app(),host="0.0.0.0",port=port)