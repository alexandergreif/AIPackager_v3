# src/app/services/instruction_processor.py

"""
Stage 1: User instruction processing
"""

import os
import json
from openai import (
    OpenAI,
    OpenAIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
)
from ..schemas import InstructionResult
from ..package_logger import get_package_logger
from .cmdlet_discovery import cmdlet_discovery_service
from ..config import Config  # Import Config

from jinja2 import Environment, FileSystemLoader


class InstructionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))

    def process_instructions(self, text: str, package_id: str) -> InstructionResult:
        package_logger = get_package_logger(package_id)

        if not self.client.api_key:
            package_logger.log_error(
                "OPENAI_API", RuntimeError("OpenAI API key not configured.")
            )
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        # Get the dynamic cmdlet reference
        cmdlet_reference = cmdlet_discovery_service.get_cmdlet_reference()

        prompt = self.jinja_env.get_template("instruction_processing.j2").render(
            user_instructions=text,
            metadata={
                "product_name": "Application",
                "version": "1.0.0",
                "file_type": "msi",
                "architecture": "x64",
            },
            cmdlet_reference=cmdlet_reference,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert in PowerShell and PSAppDeployToolkit. Return a JSON object with structured_instructions, predicted_cmdlets, and confidence_score.",
            },
            {"role": "user", "content": prompt},
        ]
        model_name = Config.AI_MODEL  # Use Config.AI_MODEL
        response_format = {"type": "json_object"}

        package_logger.log_step(
            "OPENAI_API_REQUEST",
            "Sending request to OpenAI for instruction processing",
            data={
                "model": model_name,
                "messages": messages,
                "response_format": response_format,
            },
        )

        try:
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                response_format=response_format,
            )
            response_content = response.choices[0].message.content or ""
            package_logger.log_step(
                "OPENAI_API_RESPONSE",
                "Received response from OpenAI for instruction processing",
                data={
                    "response_content": response_content,
                    "usage": response.usage.model_dump() if response.usage else None,
                },
            )
        except (APIConnectionError, APITimeoutError) as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "instruction_processing"}
            )
            raise RuntimeError(f"Unable to reach OpenAI service: {e}") from e
        except AuthenticationError as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "instruction_processing"}
            )
            raise RuntimeError(
                "Authentication with OpenAI failed. Check your API key."
            ) from e
        except OpenAIError as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "instruction_processing"}
            )
            raise RuntimeError(f"OpenAI request failed: {e}") from e

        try:
            response_data = json.loads(response_content)
            return InstructionResult(
                structured_instructions=response_data.get(
                    "structured_instructions", {}
                ),
                predicted_cmdlets=response_data.get("predicted_cmdlets", []),
                confidence_score=response_data.get("confidence_score", 0.8),
                predicted_processes_to_close=response_data.get(
                    "predicted_processes_to_close", None
                ),
            )
        except (json.JSONDecodeError, KeyError) as e:
            package_logger.log_error(
                "INSTRUCTION_PROCESSING_PARSE_ERROR",
                e,
                context={"response_content": response_content},
            )
            # Fallback for failed parsing
            return InstructionResult(
                structured_instructions={
                    "installation_type": "basic",
                    "user_instructions": text,
                },
                predicted_cmdlets=[
                    "Start-ADTMsiProcess",
                    "Show-ADTInstallationWelcome",
                    "Show-ADTInstallationProgress",
                ],
                confidence_score=0.7,
            )
