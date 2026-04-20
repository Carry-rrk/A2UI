import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from google.adk.agents.llm_agent import LlmAgent
from google.adk.models.lite_llm import LiteLlm

class TravelPlannerAgent(LlmAgent):
    def __init__(self, base_url: str, **kwargs):
        # Default to your local vLLM model
        lite_llm_model = os.getenv("LITELLM_MODEL", "openai/Qwen3.5-35B-A3B")
        super().__init__(
            name="TravelPlanner",
            model=LiteLlm(model=lite_llm_model),
            instruction="""You are a professional Travel Planner. 
            Help users plan trips to Tokyo, Paris, New York, London, or Shanghai.
            
            RULES:
            1. Use the 'get_landmarks' tool to find attractions for a city.
            2. When showing landmarks, ALWAYS use A2UI 'Card' components within a 'List'.
            3. Each card must include the landmark name, rating, description, and the local image URL provided in the data.
            4. Keep your conversational responses friendly and brief.""",
            **kwargs
        )
        self.base_url = base_url
        self.data_path = Path(__file__).parent / "data" / "travel_data.json"
        self._travel_data = self._load_data()

    def _load_data(self) -> List[Dict[str, Any]]:
        if not self.data_path.exists():
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_landmarks(self, city: str) -> str:
        """Get information about landmarks in a specific city."""
        for entry in self._travel_data:
            if entry["city"].lower() == city.lower():
                return json.dumps(entry["landmarks"], ensure_ascii=False)
        return f"Sorry, I don't have data for {city} yet. I only know about Tokyo, Paris, New York, London, and Shanghai."

    @property
    def agent_card(self) -> Dict[str, Any]:
        return {
            "name": "Travel Planner",
            "description": "Offline-first travel expert using local knowledge.",
            "iconUrl": "https://www.gstatic.com/images/icons/material/system/2x/travel_explore_black_24dp.png"
        }
