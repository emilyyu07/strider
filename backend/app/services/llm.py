"""
LLM service for semantic routing
- converts user's natrual language prompts into structured routing preferences
- uses LLama-3 via Ollama and the Instructor Library
"""

from email import message
from multiprocessing import context

import instructor, os
from openai import OpenAI


from models.llm import RoutingPreferences

#singleton LLM service instance
_llm_service=None

class LLMService:
    """
    Interacts with local LLM (Llama-3 via Ollama) 
    -> takes natrual language prompt, sends to Llama-3 with structured output instructions, returns validated RoutingPreferences object
    """

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model: str="llama3",
            timeout: int=30  
    ):
        """
        Initializes LLM service
        Args:
            base_url: Ollama API endpoint
            model: model name
            timeout: request timeout in seconds
        """

        self.model=model
        self.timeout=timeout

        #create OpenAI client for Ollama
        base_client = OpenAI(
            base_url=base_url,
            api_key="ollama",
            timeout=timeout
        )

        #wrap with instructor for structured outputs
        self.client = instructor.from_openai(base_client, mode=instructor.Mode.JSON)

    def analyze_prompt(
            self,
            prompt:str,
            context: dict | None = None
    ) -> RoutingPreferences:
       """
       Analyzes a routing prompt and extract preferences

       Args: 
       - prompt: user's natural language routing request
       - context: optional additional context (current time, user/historical preferences)

       Returns:
         - RoutingPreferences object with structured preferences

        Raises:
        - Exception if LLM request fails/response invalid
       """

       #build prompt
       system_prompt=self._build_system_prompt()
       user_message=self._build_user_message(prompt,context)

       try:
           #call llm with structured output 
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                response_model=RoutingPreferences,
                max_retries=2
            )
            return response
       
       except Exception as e:
          #log error, return default preferences
          print(f"LLM error: {e}")
          return self._get_fallback_preferences(prompt)
       
    def _build_system_prompt(self) -> str:
       """
       Builds system prompt to instruct LLM on expected output format and reasoning process
       """
       return """You are a routing preference analyzer for an intelligent running route building application.

            Your job is to analyze a user's natural language description of their desired run and extract routing preferences as cost multipliers.

            COST MULTIPLIERS EXPLAINED:
            - 1.0 = neutral (no preference)
            - Values > 1.0 = AVOID (higher = stronger avoidance)
            Examples: 2.0 (slight avoid), 10.0 (moderate avoid), 50.0 (strong avoid), 100.0 (very strong avoid)
            - Values < 1.0 = PREFER (lower = stronger preference)
            Examples: 0.8 (slight prefer), 0.5 (moderate prefer), 0.3 (strong prefer)

            ROAD TYPES:
            - motorway, trunk: Highways (usually avoid for running)
            - primary, secondary: Main roads (moderate traffic)
            - residential: Neighborhood streets (good for running)
            - path, footway: Trails and sidewalks (great for running)
            - cycleway: Bike paths (good for running)

            ATTRIBUTES:
            - scenic: Routes with high scenic value (parks, waterfronts, etc.)
            - unlit: Streets without lighting (avoid at night)

            GUIDELINES:
            1. "avoid highways/busy roads" → highway: 100.0, primary: 20.0
            2. "scenic/beautiful route" → scenic: 0.3
            3. "night run" → unlit: 10.0
            4. "quiet/peaceful" → residential: 0.7, primary: 10.0
            5. "trails/nature" → path: 0.3, footway: 0.4
            6. "well-lit" → unlit: 50.0
            7. If no strong preferences mentioned, return minimal multipliers

            Be conservative with multipliers - only add them if clearly implied by the prompt."""
    
    def _build_user_message(self, prompt: str, context: dict | None) -> str:
       """
       Builds user message for LLM, combining prompt and context
       Args:
       - prompt: user's natural language routing request
       - context: additional context (time, location, etc.)
       """

       message = f"Analyze this routing request:\n\n\"{prompt}\""

       if context:
        message += "\n\nAdditional context:"
        for key,value in context.items():
            message+=f"\n- {key}: {value}"

        return message
       
    def _get_fallback_preferences(self, prompt:str) -> RoutingPreferences:
        """
        Returns safe default preferences if llm fails
        Args:
        - prompt: original user prompt
        Returns:
        - RoutingPreferences with minimal multipliers (mostly neutral, slight highway avoidance)
        """
        prefs={}
        reasoning_parts=[]
        prompt_lower=prompt.lower()

       #highway avoidance  
        if any(word in prompt_lower for word in ["highway", "busy", "traffic", "major road"]):
            prefs["highway"]=50.0
            prefs["primary"]=20.0
            reasoning_parts.append("Avoiding major roads")

        #scenic preference
        if any(word in prompt_lower for word in ["scenic", "beautiful", "nature", "park", "waterfront"]):
            prefs["scenic"]=0.5
            reasoning_parts.append("Preferring scenic routes")

        #night safety 
        if any(word in prompt_lower for word in ["night", "dark", "evening"]):
            prefs["unlit"]=10.0
            reasoning_parts.append("Avoiding unlit roads at night")

        #trail preference
        if any(word in prompt_lower for word in ["trail", "path", "nature"]):
            prefs["path"]=0.4
            prefs["footway"]=0.5
            reasoning_parts.append("Preferring trails and sidewalks")
          
        
        reasoning="LLM Unavailable. Using fallback keyword matching to infer preferences: " 
        + "; ".join(reasoning_parts) if reasoning_parts else "LLM Unavailable. Using default routing."

        return RoutingPreferences(
            preferences=prefs,
            reasoning=reasoning,
            time_of_day=None,
            distance_preference=None
        )
    
    def get_llm_service() -> 'LLMService':
        """
        Get/create global llm service instance (singleton pattern, ensurs only one llm client is created for entire app)

        Returns:
        - LLMService instance
        """
        global _llm_service
        if _llm_service is None:
            _llm_service = LLMService()
        return _llm_service