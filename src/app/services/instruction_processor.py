# src/app/services/instruction_processor.py

"""
Stage 1: User instruction processing
"""

import os
from openai import OpenAI
from ..schemas import InstructionResult


from jinja2 import Environment, FileSystemLoader


class InstructionProcessor:
    def __init__(self) -> None:
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        self.jinja_env = Environment(loader=FileSystemLoader("src/app/prompts"))

    def process_instructions(self, text: str) -> InstructionResult:
        prompt = self.jinja_env.get_template("instruction_processing.j2").render(
            user_instructions=text
        )

        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert in PowerShell and PSAppDeployToolkit.",
                },
                {"role": "user", "content": prompt},
            ],
            response_model=InstructionResult,
        )

        assert isinstance(response, InstructionResult)
        return response
