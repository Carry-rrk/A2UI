from typing import Any, AsyncGenerator, Dict, List
from google.adk.agents.base_agent import BaseAgent
from a2a.server.request_handlers import AgentExecutor
from a2ui.schema.constants import VERSION_0_9
from a2ui.schema.manager import A2uiSchemaManager, CatalogConfig

class TravelPlannerAgentExecutor(AgentExecutor):
    def __init__(self, agent: BaseAgent):
        self.agent = agent
        self.a2ui_manager = A2uiSchemaManager(
            CatalogConfig(version=VERSION_0_9)
        )

    async def execute(
        self, 
        task_id: str, 
        messages: List[Dict[str, Any]], 
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        
        # Add basic tool definitions for the LLM
        tools = [
            {
                "name": "get_landmarks",
                "description": "Get top attractions for a city. Supported cities: Tokyo, Paris, New York, London, Shanghai.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {"type": "string"}
                    },
                    "required": ["city"]
                }
            }
        ]

        # Call the agent (this uses LiteLLM via the agent's model)
        async for part in self.agent.run_async(messages, tools=tools):
            # In a real ADK implementation, run_async handles tool calling.
            # Here we simplify for the demo structure.
            yield part

    def get_a2ui_capabilities(self) -> Dict[str, Any]:
        return {
            "supported_versions": [VERSION_0_9],
            "static_catalog": self.a2ui_manager.get_catalog(VERSION_0_9)
        }
