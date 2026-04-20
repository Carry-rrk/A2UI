import logging
import os
import traceback
import click
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from agent import TravelPlannerAgent
from agent_executor import TravelPlannerAgentExecutor
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

# Load configurations
load_dotenv()
load_dotenv("../../../.env")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10008)
def main(host, port):
    try:
        lite_llm_model = os.getenv("LITELLM_MODEL", "openai/Qwen3.5-35B-A3B")
        logger.info(f"Initializing Travel Planner with model: {lite_llm_model}")
        
        base_url = f"http://{host}:{port}"
        agent = TravelPlannerAgent(base_url=base_url)
        agent_executor = TravelPlannerAgentExecutor(agent)

        request_handler = DefaultRequestHandler(
            agent_executor=agent_executor,
            task_store=InMemoryTaskStore(),
        )
        
        server = A2AStarletteApplication(
            agent_card=agent.agent_card, 
            http_handler=request_handler
        )
        
        import uvicorn
        app = server.build()

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"], # For development
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # Mount the images directory to serve local photos
        image_path = os.path.join(os.path.dirname(__file__), "data", "images")
        app.mount("/static", StaticFiles(directory=image_path), name="static")

        logger.info(f"Travel Planner running at {base_url}")
        uvicorn.run(app, host=host, port=port)
        
    except Exception as e:
        logger.error(f"Failed to start Travel Planner: {e} {traceback.format_exc()}")
        exit(1)

if __name__ == "__main__":
    main()
