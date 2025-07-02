# src/app/services/advisor_service.py

"""
Stage 5: Self-correction AI
"""

import os
import json
from typing import Optional, Dict
from openai import (
    OpenAI,
    OpenAIError,
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
)

from jinja2 import Environment, FileSystemLoader
from ..schemas import PSADTScript
from ..package_logger import get_package_logger
from .rag_service import RAGService
from .psadt_documentation_parser import PSADTDocumentationParser, CmdletDefinition
from ..config import Config  # Import Config


class AdvisorService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))

        # Initialize PSADT v4 documentation parser
        self.psadt_parser = PSADTDocumentationParser()
        self.psadt_cmdlets: Optional[Dict[str, CmdletDefinition]] = None
        self._load_psadt_cmdlets()

    def _load_psadt_cmdlets(self) -> None:
        """Load PSADT v4 cmdlet definitions for corrections"""
        try:
            self.psadt_cmdlets = self.psadt_parser.parse_all_cmdlets()
        except Exception:
            # Fallback to empty dict if cmdlets can't be loaded
            self.psadt_cmdlets = {}

    def correct_script(
        self, script: PSADTScript, hallucination_report: dict, package_id: str
    ) -> PSADTScript:
        package_logger = get_package_logger(package_id)
        self.rag_service = RAGService(package_id=package_id)

        if not self.client.api_key:
            package_logger.log_error(
                "OPENAI_API", RuntimeError("OpenAI API key not configured.")
            )
            raise RuntimeError(
                "OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )

        # Build comprehensive PSADT v4 cmdlet reference for corrections
        cmdlet_reference = self._build_psadt_v4_reference(hallucination_report)

        # Also get RAG documentation for any unknown cmdlets
        unknown_cmdlets = []
        for issue in hallucination_report.get("issues", []):
            if issue.get("type") == "unknown_cmdlets":
                unknown_cmdlets.extend(issue.get("cmdlets", []))

        # Note: RAG documentation available if needed for unknown cmdlets
        # Currently using comprehensive PSADT v4 reference instead

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
        model_name = Config.AI_MODEL  # Use Config.AI_MODEL
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

    def _build_psadt_v4_reference(self, hallucination_report: dict) -> str:
        """Build comprehensive PSADT v4 cmdlet reference for AI corrections"""
        if not self.psadt_cmdlets:
            return "PSADT v4 cmdlets not available. Use only PSADT v4 ADT- prefixed cmdlets."

        # Extract cmdlets and parameters from hallucination issues
        relevant_cmdlets = set()
        parameter_issues = []

        for issue in hallucination_report.get("issues", []):
            if issue.get("cmdlet"):
                relevant_cmdlets.add(issue["cmdlet"])
            if issue.get("type") == "invalid_parameter":
                parameter_issues.append(
                    {
                        "cmdlet": issue.get("cmdlet"),
                        "invalid_param": issue.get("parameter"),
                        "suggestions": issue.get("suggestions", []),
                    }
                )

        # Build reference with correct cmdlet information
        reference_parts = [
            "# PSADT v4 Cmdlet Reference for Corrections",
            "",
            "## CRITICAL: Always use PSADT v4 cmdlets (ADT- prefix), never use v3 cmdlets or standard PowerShell cmdlets.",
            "",
            "## Common v3 → v4 Mappings:",
            "- Execute-Process → Start-ADTProcess",
            "- Execute-MSI → Start-ADTMsiProcess",
            "- Write-Log → Write-ADTLogEntry",
            "- Copy-File → Copy-ADTFile",
            "- Set-RegistryKey → Set-ADTRegistryKey",
            "- Copy-Item → Copy-ADTFile (with correct parameters)",
            "",
            "## Cmdlets Referenced in Script Issues:",
            "",
        ]

        # Add specific cmdlet information
        for cmdlet in relevant_cmdlets:
            if cmdlet in self.psadt_cmdlets:
                cmdlet_def = self.psadt_cmdlets[cmdlet]
                reference_parts.append(f"### {cmdlet}")

                if cmdlet_def.synopsis:
                    reference_parts.append(f"**Synopsis**: {cmdlet_def.synopsis}")

                if cmdlet_def.parameters:
                    reference_parts.append("**Valid Parameters**:")
                    for param_name, param_def in list(cmdlet_def.parameters.items())[
                        :10
                    ]:  # Limit to avoid too long
                        param_info = f"  - `-{param_name}`: {param_def.type.value}"
                        if param_def.mandatory:
                            param_info += " (Required)"
                        if param_def.default_value:
                            param_info += f" (Default: {param_def.default_value})"
                        if param_def.valid_values:
                            param_info += (
                                f" (Valid: {', '.join(param_def.valid_values[:5])})"
                            )
                        reference_parts.append(param_info)

                if cmdlet_def.examples:
                    reference_parts.append("**Example Usage**:")
                    example = cmdlet_def.examples[0]  # Use first example
                    reference_parts.append(f"```powershell\n{example.code}\n```")

                reference_parts.append("")

        # Add parameter correction guidance
        if parameter_issues:
            reference_parts.extend(["## Parameter Corrections Needed:", ""])

            for issue in parameter_issues:
                cmdlet = issue["cmdlet"]
                invalid_param = issue["invalid_param"]
                suggestions = issue["suggestions"]

                if cmdlet in self.psadt_cmdlets:
                    valid_params = list(self.psadt_cmdlets[cmdlet].parameters.keys())[
                        :5
                    ]
                    reference_parts.append(
                        f"- **{cmdlet}**: Remove invalid parameter `-{invalid_param}`"
                    )
                    if suggestions:
                        reference_parts.append(f"  → Use: -{', -'.join(suggestions)}")
                    elif valid_params:
                        reference_parts.append(
                            f"  → Valid parameters: -{', -'.join(valid_params)}"
                        )

        # Add general guidelines
        reference_parts.extend(
            [
                "",
                "## Correction Guidelines:",
                "1. **ONLY use PSADT v4 cmdlets** with ADT- prefix",
                "2. **Remove invalid parameters** completely",
                "3. **Use correct parameter names** from the reference above",
                "4. **Maintain PSADT v4 compliance** - no fallback to v3 or PowerShell cmdlets",
                "5. **Preserve script functionality** while fixing parameter issues",
                "",
                f"## Available PSADT v4 Cmdlets ({len(self.psadt_cmdlets)} total):",
                ", ".join(sorted(self.psadt_cmdlets.keys())[:20]) + " ...",
            ]
        )

        return "\n".join(reference_parts)
