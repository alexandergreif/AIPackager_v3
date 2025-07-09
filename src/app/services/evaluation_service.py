# src/app/services/evaluation_service.py
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Any, Optional

from ..schemas import (
    EvaluationResult,
    ModelInfo,
    Scenario,
    EvaluationMetrics,
    PSADTScript,
)
from ..package_logger import get_package_logger
from .script_generator import PSADTGenerator
from ..models import Package, Metadata
from ..script_renderer import ScriptRenderer


class EvaluationService:
    """Service for handling model evaluations."""

    def __init__(self, instance_dir: Path):
        """
        Initializes the EvaluationService.

        Args:
            instance_dir: The path to the application's instance directory.
        """
        self.evaluations_dir = instance_dir / "evaluations"
        self.logs_dir = instance_dir / "logs" / "evaluations"
        self.data_dir = Path(__file__).parent.parent / "data"
        self.evaluations_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _load_json_data(self, file_path: Path) -> Any:
        """Loads data from a JSON file."""
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def get_scenarios(self) -> List[Scenario]:
        """Retrieves all available test scenarios."""
        scenarios_data = self._load_json_data(self.data_dir / "scenarios.json")
        if scenarios_data:
            return [Scenario(**s) for s in scenarios_data]
        return []

    def get_models(self) -> List[ModelInfo]:
        """Retrieves all available models."""
        models_data = self._load_json_data(self.data_dir / "models.json")
        if models_data and "models" in models_data:
            return [ModelInfo(**m) for m in models_data["models"]]
        return []

    def get_advisor_model(self) -> Optional[ModelInfo]:
        """Retrieves the advisor model."""
        models_data = self._load_json_data(self.data_dir / "models.json")
        if models_data and "advisor_model" in models_data:
            return ModelInfo(**models_data["advisor_model"])
        return None

    def get_all_evaluations(self) -> List[EvaluationResult]:
        """Retrieves all past evaluation results."""
        evaluations = []
        for file_path in self.evaluations_dir.glob("*.json"):
            eval_data = self._load_json_data(file_path)
            if eval_data:
                evaluations.append(EvaluationResult(**eval_data))
        evaluations.sort(key=lambda x: x.timestamp, reverse=True)
        return evaluations

    def get_evaluation(self, evaluation_id: str) -> Optional[EvaluationResult]:
        """Retrieves a single evaluation result by its ID."""
        file_path = self.evaluations_dir / f"{evaluation_id}.json"
        eval_data = self._load_json_data(file_path)
        if eval_data:
            return EvaluationResult(**eval_data)
        return None

    def get_evaluation_log_content(self, log_path: str) -> Optional[str]:
        """Reads the content of a log file."""
        try:
            with open(log_path, "r") as f:
                return f.read()
        except FileNotFoundError:
            return None

    def run_evaluation(
        self, model_id: str, scenario_id: str
    ) -> Optional[EvaluationResult]:
        """Runs a new evaluation using the live 5-stage pipeline."""
        models = {m.id: m for m in self.get_models()}
        scenarios = {s.id: s for s in self.get_scenarios()}

        if model_id not in models or scenario_id not in scenarios:
            return None

        selected_model = models[model_id]
        selected_scenario = scenarios[scenario_id]
        evaluation_id = str(uuid.uuid4())

        logger = get_package_logger(evaluation_id)
        logger.log_step(
            "INIT",
            f"Starting live evaluation for model '{selected_model.name}' on scenario '{selected_scenario.title}'.",
        )

        try:
            # Create a temporary Package and Metadata object for the pipeline
            temp_metadata = Metadata(
                product_name=selected_scenario.psadt_variables.get("app_name"),
                version=selected_scenario.psadt_variables.get("app_version"),
                publisher=selected_scenario.psadt_variables.get("app_vendor"),
                architecture=selected_scenario.psadt_variables.get("app_arch"),
                language=selected_scenario.psadt_variables.get("app_lang"),
            )
            temp_package = Package(
                id=uuid.UUID(evaluation_id),
                filename=f"{selected_scenario.title}.msi",
                file_path="/tmp/fake_path",
                custom_instructions=selected_scenario.prompt,
                package_metadata=temp_metadata,  # Associate metadata
            )

            # Instantiate the pipeline generator
            generator = PSADTGenerator()

            # Run the 5-stage pipeline - Note: session=None for evaluation mode
            pipeline_result: PSADTScript = generator.generate_script(
                text=selected_scenario.prompt,
                package=temp_package,
                model_name=selected_model.id,
                package_logger=logger,
                session=None,  # Explicitly pass None for evaluation mode
            )

            # Process the results
            hallucination_report = pipeline_result.hallucination_report or {}
            corrections_log = pipeline_result.corrections_applied or []

            # Calculate metrics from live results
            num_found = len(hallucination_report.get("issues", []))
            num_corrected = len(corrections_log)
            trust_score = (num_corrected / num_found) if num_found > 0 else 1.0

            metrics = EvaluationMetrics(
                hallucinations_found=num_found,
                hallucinations_corrected=num_corrected,
                trust_score=trust_score,
            )
            logger.log_step(
                "METRICS_CALC", "Live metrics calculated.", data=metrics.model_dump()
            )

            # Get raw and corrected script outputs
            renderer = ScriptRenderer()
            raw_output = renderer.render_psadt_script(
                temp_package, pipeline_result.model_dump()
            )
            corrected_output = raw_output  # Default to raw if no corrections
            if pipeline_result.corrections_applied:
                # Re-render with the final script state if corrections were applied
                final_script_sections = pipeline_result.model_dump()
                corrected_output = renderer.render_psadt_script(
                    temp_package, final_script_sections
                )

            log_file_path = logger.get_log_file_path()
            result = EvaluationResult(
                id=evaluation_id,
                model=selected_model,
                scenario=selected_scenario,
                timestamp=datetime.now(timezone.utc).isoformat(),
                raw_model_output=raw_output,
                advisor_corrected_output=corrected_output,
                evaluation_log=str(log_file_path) if log_file_path else "",
                metrics=metrics,
                detailed_hallucination_report=hallucination_report.get("issues", []),
                detailed_corrections_log=corrections_log,
            )

            # Save result to disk
            with open(self.evaluations_dir / f"{result.id}.json", "w") as f:
                json.dump(result.model_dump(), f, indent=2)
            logger.log_step(
                "SAVE_RESULT",
                f"Live evaluation result saved to {self.evaluations_dir / f'{result.id}.json'}",
            )

            return result

        except Exception as e:
            logger.log_error("EVALUATION_PIPELINE_FAILED", e)
            return None
