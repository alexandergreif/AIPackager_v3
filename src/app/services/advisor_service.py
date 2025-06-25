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

        self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in PowerShell and PSAppDeployToolkit.",
                },
                {"role": "user", "content": prompt},
            ],
        )

        # corrected_script_str = response.choices[0].message.content

        # This is a placeholder for parsing the corrected script string
        # back into a PSADTScript object.

        script.corrections_applied = ["Placeholder correction"]
        return script
