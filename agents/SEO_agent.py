"""SEO agent runs on port 8002

WHAT IT DOES:
  Receives the polished article and returns structured SEO metadata:
  - SEO-optimised title (60 chars)
  - Meta description (155 chars)
  - Primary keyword
  - Secondary keywords (5)
  - Suggested URL slug
  - Estimated reading time
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

port=8004

seo_metadata_skill=AgentSkill(
    id="generate_seo_metadata",
    name="Generate SEO Metadata",
    description=(
        "analyses an article and produces SEO optimised metadata"
        "title,meta description,keyword ,URL slug and reading time"

    ),
    tags=["seo","metadata","keywords","search-optimization"],
    examples=["generates seo metadata for this article,....",
              "WHat keywords shoudl i use for this content?",],

    inputModes=["text/plain"],
    outputModes=["text/plain"],
)

keyword_research_skill =AgentSkill(
    id="keyword_research",
    name="Keyword Research",
    description=("Given a topic or article suggest a hierarchy of target keywords"
                 "ranked by search intent and relevance"),
    tags=["seo","keywords","research"],
    example=["What keywords should i target for an article about solar energy?"],
    inputModes=["text/plain"],
    outputModes=["text/plain"]
    )

seo_agent_card=AgentCard(
    name="SEO Agent",
    description="generates seo metadata and keyword suggestions for articles",
    url=f"http://localhost:{port}/",
    version="1.0.0",
    defaultInputModes=["text/plain"],
    defaultOutputModes=["text/plain"],
    capabilities=AgentCapabilities(streaming=False),
    authentication=AgentAuthentication(schemes=["public"]),
    skills=[seo_metadata_skill,keyword_research_skill]
)

class SEOAgentExecutor(AgentExecutor):
    """Generates SEO metadata from the polished article text"""

    async def execute(
            self,
            context:RequestContext,
            event_queue:EvenetQueue,
    )->None:
        article = context.get_user_input()
        prompt=f"""You are an SEO expert. Analyse the following article and
generate SEO metadata. Return EXACTLY in this format (no extra text):
 
SEO TITLE (max 60 chars):
[title here]
 
META DESCRIPTION (max 155 chars):
[description here]
 
PRIMARY KEYWORD:
[one main keyword phrase]
 
SECONDARY KEYWORDS (5):
1. [keyword]
2. [keyword]
3. [keyword]
4. [keyword]
5. [keyword]
 
URL SLUG:
[hyphenated-url-slug]
 
ESTIMATED READING TIME:
[X minutes]
 
ARTICLE:
{article[:3000]}
        """
        seo_text=await asyncio.to_thread(call_gemini,prompt)
        event_queue.enqueue_event(new_agent_text_message(seo_text))

    
    async def cancel(self,context:RequestContext,event_queue:EventQueue)->None:
        raise NotImplementedError("SEO agent does not support cancellation")
    

def build_app():
    return A2AStarletteApplication(
        agent_card=seo_agent_card,
        http_handler=DefaultRequestHandler(
            agent_executor=SEOAgentExecutor(),
            task_store=InMemoryTaskStore,
        ),
    ).build()

if __name__ == "__main__":
    print(f"SEOAgent starting on http://localhost:{port}")
    print(f"SEOagent age nt card:http://localhost:{port}/.well-known/agent.json")
    uvicorn.run(build_app(),host="0.0.0.0",port=port)