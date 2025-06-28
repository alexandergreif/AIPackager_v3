# src/app/services/instruction_processor.py

"""
Stage 1: User instruction processing
"""

import os
from openai import OpenAI, OpenAIError, APIConnectionError, APITimeoutError, AuthenticationError
from ..schemas import InstructionResult


from jinja2 import Environment, FileSystemLoader


class InstructionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))

    def process_instructions(self, text: str) -> InstructionResult:
        if not self.client.api_key:
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        prompt = self.jinja_env.get_template("instruction_processing.j2").render(
            user_instructions=text,
            metadata={
                "product_name": "Application",
                "version": "1.0.0",
                "file_type": "msi",
                "architecture": "x64",
            },
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert in PowerShell and PSAppDeployToolkit. "
                            "Return a JSON object with structured_instructions, predicted_cmdlets, "
                            "predicted_processes_to_close, and confidence_score."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
        except (APIConnectionError, APITimeoutError) as e:
            raise RuntimeError(f"Unable to reach OpenAI service: {e}") from e
        except AuthenticationError as e:
            raise RuntimeError(
                "Authentication with OpenAI failed. Check your API key."
            ) from e
        except OpenAIError as e:
            raise RuntimeError(f"OpenAI request failed: {e}") from e

        import json

        try:
            response_data = json.loads(response.choices[0].message.content or "")
            return InstructionResult(
                structured_instructions=response_data.get(
                    "structured_instructions", {}
                ),
                predicted_cmdlets=response_data.get("predicted_cmdlets", []),
                confidence_score=response_data.get("confidence_score", 0.8),
                predicted_processes_to_close=response_data.get(
                    "predicted_processes_to_close"
                ),
            )
        except (json.JSONDecodeError, KeyError):
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
                predicted_processes_to_close=None,
            )
