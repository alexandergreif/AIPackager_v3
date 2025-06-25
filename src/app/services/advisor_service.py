# src/app/services/advisor_service.py

"""
Stage 5: Self-correction AI
"""

import os
from openai import OpenAI
from jinja2 import Environment, FileSystemLoader
from ..schemas import PSADTScript


class AdvisorService:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))

    def correct_script(
        self, script: PSADTScript, hallucination_report: dict
    ) -> PSADTScript:
        prompt = self.jinja_env.get_template("advisor_correction.j2").render(
            original_script=script.model_dump_json(indent=4),
            hallucination_report=hallucination_report,
        )

        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in PowerShell and PSAppDeployToolkit. Return a corrected PSADTScript JSON object.",
                },
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
        )

        corrected_script_str = response.choices[0].message.content

        # Parse the corrected script string back into a PSADTScript object
        try:
            import json

            corrected_data = json.loads(corrected_script_str or "")

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

        except (json.JSONDecodeError, KeyError) as e:
            # Fallback: apply minimal corrections
            script.corrections_applied = [
                f"Applied basic corrections due to parsing error: {str(e)}"
            ]

        return script
