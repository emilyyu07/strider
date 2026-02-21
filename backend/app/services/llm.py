"""
LLM service for semantic routing
- converts user's natrual language prompts into structured routing preferences
- uses LLama-3 via Ollama and the Instructor Library
"""

import instructor, os
from openai import OpenAI
from typing import Optional

from models.llm import RoutingPreferences

class LLMService:
    """
    Interacts with local LLM (Llama-3 via Ollama) 
    -> takes natrual language prompt, sends to Llama-3 with structured output instructions, returns validated RoutingPreferences object
    """

    def __init__(
            self,
            base_url: str = "http://localhost:11434",
            model: str="llama-3",
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
       