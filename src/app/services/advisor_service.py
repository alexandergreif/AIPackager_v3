# src/app/services/advisor_service.py

"""
Stage 5: Self-correction AI
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
from dotenv import load_dotenv

from jinja2 import Environment, FileSystemLoader
from ..schemas import PSADTScript
from ..package_logger import get_package_logger
from .rag_service import RAGService


class AdvisorService:
    def __init__(self) -> None:
        load_dotenv()  # Load environment variables from .env file
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))
        self.rag_service = RAGService()

    def correct_script(
        self, script: PSADTScript, hallucination_report: dict, package_id: str
    ) -> PSADTScript:
        package_logger = get_package_logger(package_id)

        if not self.client.api_key:
            package_logger.log_error(
                "OPENAI_API", RuntimeError("OpenAI API key not configured.")
            )
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        unknown_cmdlets = []
        for issue in hallucination_report.get("issues", []):
            if issue.get("type") == "unknown_cmdlets":
                unknown_cmdlets.extend(issue.get("cmdlets", []))

        if unknown_cmdlets:
            cmdlet_reference = self.rag_service.query(unknown_cmdlets)
        else:
            cmdlet_reference = (
                "No unknown cmdlets found. Using standard cmdlet reference."
            )

        prompt = self.jinja_env.get_template("advisor_correction.j2").render(
            original_script=script.model_dump_json(indent=4),
            hallucination_report=hallucination_report,
            cmdlet_reference=cmdlet_reference,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert in PowerShell and PSAppDeployToolkit. Return a corrected PSADTScript JSON object.",
            },
            {"role": "user", "content": prompt},
        ]
        model_name = "gpt-4.1-mini"
        response_format = {"type": "json_object"}

        package_logger.log_step(
            "OPENAI_API_REQUEST",
            "Sending request to OpenAI for advisor correction",
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
            corrected_script_str = response.choices[0].message.content or ""
            package_logger.log_step(
                "OPENAI_API_RESPONSE",
                "Received response from OpenAI for advisor correction",
                data={
                    "response_content": corrected_script_str,
                    "usage": response.usage.model_dump() if response.usage else None,
                },
            )
        except (APIConnectionError, APITimeoutError) as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "advisor_correction"}
            )
            raise RuntimeError(f"Unable to reach OpenAI service: {e}") from e
        except AuthenticationError as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "advisor_correction"}
            )
            raise RuntimeError(
                "Authentication with OpenAI failed. Check your API key."
            ) from e
        except OpenAIError as e:
            package_logger.log_error(
                "OPENAI_API", e, context={"stage": "advisor_correction"}
            )
            raise RuntimeError(f"OpenAI request failed: {e}") from e

        # Parse the corrected script string back into a PSADTScript object
        try:
            corrected_data = json.loads(corrected_script_str)

            # Update the original script with corrected data
            if "pre_installation_tasks" in corrected_data:
                script.pre_installation_tasks = corrected_data["pre_installation_tasks"]
            if "installation_tasks" in corrected_data:
                script.installation_tasks = corrected_data["installation_tasks"]
            if "post_installation_tasks" in corrected_data:
                script.post_installation_tasks = corrected_data[
                    "post_installation_tasks"
                ]
            if "uninstallation_tasks" in corrected_data:
                script.uninstallation_tasks = corrected_data["uninstallation_tasks"]
            if "post_uninstallation_tasks" in corrected_data:
                script.post_uninstallation_tasks = corrected_data[
                    "post_uninstallation_tasks"
                ]

            # Add correction tracking
            corrections = []
            for issue in hallucination_report.get("issues", []):
                if issue.get("type") == "unknown_cmdlets":
                    corrections.append(
                        f"Corrected unknown cmdlets: {', '.join(issue.get('cmdlets', []))}"
                    )
                else:
                    corrections.append(
                        f"Applied correction for: {issue.get('type', 'unknown issue')}"
                    )

            script.corrections_applied = corrections
            package_logger.log_step(
                "ADVISOR_CORRECTION_SUCCESS", "Script corrected successfully."
            )

        except (json.JSONDecodeError, KeyError) as e:
            package_logger.log_error(
                "ADVISOR_CORRECTION_PARSE_ERROR",
                e,
                context={"response_content": corrected_script_str},
            )
            # Fallback: apply minimal corrections
            script.corrections_applied = [
                f"Applied basic corrections due to parsing error: {str(e)}"
            ]

        return script
