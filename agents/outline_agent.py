"""outline agent runs on port 8001

WHAT IT DOES:
  Receives a writing topic (e.g. "The future of renewable energy in Nepal")
  and returns a structured outline with 5 sections: Introduction, 3 body
  sections, and a Conclusion.
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
from llm.gemini_client import call_gemin

PORT=8001

outline_skill = AgentSkill(
    id= "create_outline",
    name="Create Writing Outline",
    description=(
        """Given a writing topic,produce a strctured 5 section outline"""
        """with Introduction, three body section and Conclusion"""
        """Each section include a title and 2-3 bullet points"""
    ),
    tags=["writing","outline","structure","planning"],
    example=[
        """The future of renewable energy""",
        """Why python is popular for data science""",
        """Health benefit of morning exercise"""
    ],
    inputModes=["text/plain"],
    outputModes=["text/plain"],
)


outline_agent_card = AgentCard(
    name="outline agent",
    description="Created strctured writing outline from a topic",
    url=f"http://localhost:{PORT}/",
    version="1.0.0",
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False),
    authentication=AgentAuthentication(schemes=["public"]),
    skills=[outline_skill],
)

class OutlineAgentExecutor(AgentExecutor):
    """
    Processes an incoming topic request, calls Gemini , and returns an outline
    """

    async def execute(
            self,
            context:RequestContext,
            event_queue:EvenetQueue,
    )->None:
        topic=context.get_user_input() #input of user
        prompt=f"""You are a professiona; content startegist.
        create a detailed writing outline for following topic
         TOPIC: {topic}
 
FORMAT YOUR RESPONSE EXACTLY LIKE THIS:
 
# OUTLINE: {topic}
 
## 1. Introduction
- Hook/attention grabber idea
- Background context
- Thesis statement direction
 
## 2. [First Main Section Title]
- Key point 1
- Key point 2
- Supporting data or example
 
## 3. [Second Main Section Title]
- Key point 1
- Key point 2
- Supporting data or example
 
## 4. [Third Main Section Title]
- Key point 1
- Key point 2
- Supporting data or example
 
## 5. Conclusion
- Summary of key points
- Call to action or final thought
- Memorable closing line
 
Only output the outline. No preamble or commentary. """
        
        outline_text=await 