"""AI Gateway for Nudgeline."""

from __future__ import annotations

import logging
from typing import Any

from modules.tenancy.domain.settings import get_settings
import yaml
from pathlib import Path

logger = logging.getLogger(__name__)


class AIGateway:
    """Routes LLM requests according to model config and privacy rules."""

    def __init__(self, config_path: str = "config/models.yaml"):
        self.config_path = config_path
        self._load_config()

    def _load_config(self) -> None:
        """Load model configuration from yaml."""
        try:
            with open(self.config_path, "r") as f:
                self.config = yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load model config: {e}")
            self.config = {"providers": {}, "tasks": {}}

    async def generate_completion(
        self,
        task: str,
        messages: list[dict[str, str]],
        contains_pii: bool = True
    ) -> str:
        """Generate a completion for a specific task.
        
        Args:
            task: The task name (e.g. 'live_turn', 'extraction')
            messages: Conversation history/prompts
            contains_pii: Whether the prompt contains lead PII.
        """
        task_config = self.config.get("tasks", {}).get(task)
        if not task_config:
            raise ValueError(f"Unknown AI task: {task}")
            
        provider_name = task_config.get("provider")
        model = task_config.get("model")
        
        provider_config = self.config.get("providers", {}).get(provider_name, {})
        
        # Security/Privacy Enforcement
        if contains_pii and not provider_config.get("allowed_for_pii", False):
            raise PermissionError(
                f"Provider {provider_name} is not allowed to process PII data."
            )
            
        logger.info(f"Routing to {provider_name} ({model}) for task {task}")
        
        # MVP: Return a fake response instead of actually calling LLM APIs
        # In a real environment we would switch between OpenAI-compatible clients (Groq, vLLM)
        # or the Gemini SDK.
        return self._fake_completion(task)

    def _fake_completion(self, task: str) -> str:
        """Return a fake response for testing without API keys."""
        if task == "live_turn":
            return "Hello, this is a simulated response from the AI."
        elif task == "extraction":
            return '{"outcome": "NOT_INTERESTED", "summary": "Simulated extraction"}'
        return "Simulated response"
