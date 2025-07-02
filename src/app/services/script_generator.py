# src/app/services/script_generator.py

"""
5-stage pipeline orchestrator
"""

from .instruction_processor import InstructionProcessor
from .rag_service import RAGService
from .hallucination_detector import HallucinationDetector
from .advisor_service import AdvisorService
from ..schemas import PSADTScript, InstructionResult
from ..utils import retry_with_backoff
from ..workflow.progress import pct
from ..logging_cmtrace import get_cmtrace_logger
from ..package_logger import get_package_logger
from typing import ContextManager
import queue
from ..config import Config  # Import Config

try:
    from prometheus_client import Summary  # type: ignore
except Exception:  # pragma: no cover - optional dependency

    class Summary:  # type: ignore
        def __init__(self, *_: object, **__: object) -> None:
            pass

        def labels(self, *_: object, **__: object) -> "Summary":  # type: ignore
            return self

        def time(self) -> ContextManager[None]:  # type: ignore
            from contextlib import nullcontext

            return nullcontext()


from sqlalchemy.orm import Session
from ..models import Package


logger_cm = get_cmtrace_logger("pipeline")
PIPELINE_STAGE_SECONDS = Summary(
    "pipeline_stage_seconds", "Time spent in pipeline stage", ["stage"]
)


class PSADTGenerator:
    def __init__(self) -> None:
        self.instruction_processor = InstructionProcessor()
        self.rag_service = RAGService()
        self.hallucination_detector = HallucinationDetector()
        self.advisor_service = AdvisorService()

    @retry_with_backoff()
    def generate_script(
        self,
        text: str,
        package: Package | None = None,
        session: Session | None = None,
        progress_queue: queue.Queue | None = None,
    ) -> PSADTScript:
        """
        5-stage pipeline for generating validated PSADT scripts.
        """
        package_id = str(package.id) if package else "unknown_package"
        package_logger = get_package_logger(package_id)

        # Stage 1: Instruction Processing
        if not package or not package.instruction_result:
            package_logger.log_5_stage_pipeline(
                1, "Instruction Processing", "START", {"user_instructions": text}
            )
            with PIPELINE_STAGE_SECONDS.labels("instruction_processing").time():
                instruction_result = self.instruction_processor.process_instructions(
                    text, package_id
                )
            if package and session:
                package.instruction_result = instruction_result.model_dump()
                package.current_step = "instruction_processing"
                package.progress_pct = pct("instruction_processing")
                session.commit()
                if progress_queue:
                    progress_queue.put(
                        {
                            "status": "processing",
                            "progress": package.progress_pct,
                            "current_step": "Instruction Processing",
                            "stage_number": 1,
                        }
                    )
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "instruction_processing",
                    pct("instruction_processing"),
                )
            package_logger.log_5_stage_pipeline(
                1,
                "Instruction Processing",
                "COMPLETED",
                {"instruction_result": instruction_result.model_dump()},
            )
        else:
            instruction_result = (
                InstructionResult(**package.instruction_result)
                if package and package.instruction_result
                else InstructionResult(
                    structured_instructions={},
                    predicted_cmdlets=[],
                    confidence_score=0.0,
                )
            )

        # Update package metadata with predicted processes if MSI parsing failed
        if (
            package
            and package.package_metadata
            and (
                not package.package_metadata.executable_names
                or len(package.package_metadata.executable_names) == 0
            )
            and instruction_result.predicted_processes_to_close
            and len(instruction_result.predicted_processes_to_close) > 0
            and session
        ):
            package.package_metadata.executable_names = (
                instruction_result.predicted_processes_to_close
            )
            session.add(package.package_metadata)
            session.commit()
            package_logger.log_step(
                "EXECUTABLE_NAMES_UPDATED",
                "Executable names updated with AI predicted processes.",
                data={
                    "predicted_processes": instruction_result.predicted_processes_to_close
                },
            )

        # Stage 2: Targeted RAG
        if not package or not package.rag_documentation:
            package_logger.log_5_stage_pipeline(
                2,
                "Targeted RAG",
                "START",
                {"predicted_cmdlets": instruction_result.predicted_cmdlets},
            )
            with PIPELINE_STAGE_SECONDS.labels("rag_enrichment").time():
                rag_documentation = self.rag_service.query(
                    instruction_result.predicted_cmdlets
                )
            if package and session:
                # Convert dict to JSON string for database storage
                import json

                package.rag_documentation = (
                    json.dumps(rag_documentation)
                    if isinstance(rag_documentation, dict)
                    else rag_documentation
                )
                package.current_step = "rag_enrichment"
                package.progress_pct = pct("rag_enrichment")
                session.commit()
                if progress_queue:
                    progress_queue.put(
                        {
                            "status": "processing",
                            "progress": package.progress_pct,
                            "current_step": "Targeted RAG",
                            "stage_number": 2,
                        }
                    )
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "rag_enrichment",
                    pct("rag_enrichment"),
                )
            package_logger.log_5_stage_pipeline(
                2,
                "Targeted RAG",
                "COMPLETED",
                {"rag_documentation_length": len(rag_documentation)},
            )
        else:
            rag_documentation = package.rag_documentation if package else ""

        # Stage 3: Script Generation
        if not package or not package.initial_script:
            package_logger.log_5_stage_pipeline(
                3,
                "Script Generation",
                "START",
                {
                    "instruction_result": instruction_result.model_dump(),
                    "rag_documentation_length": len(rag_documentation),
                },
            )
            with PIPELINE_STAGE_SECONDS.labels("script_generation").time():
                initial_script = self._generate_initial_script(
                    instruction_result, rag_documentation, package
                )
            if package and session:
                package.initial_script = initial_script.model_dump()
                package.current_step = "script_generation"
                package.progress_pct = pct("script_generation")
                session.commit()
                if progress_queue:
                    progress_queue.put(
                        {
                            "status": "processing",
                            "progress": package.progress_pct,
                            "current_step": "Script Generation",
                            "stage_number": 3,
                        }
                    )
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "script_generation",
                    pct("script_generation"),
                )
            package_logger.log_5_stage_pipeline(
                3,
                "Script Generation",
                "COMPLETED",
                {"initial_script": initial_script.model_dump()},
            )
        else:
            initial_script = (
                PSADTScript(**package.initial_script)
                if package and package.initial_script
                else PSADTScript(
                    pre_installation_tasks=[],
                    installation_tasks=[],
                    post_installation_tasks=[],
                    uninstallation_tasks=[],
                    post_uninstallation_tasks=[],
                )
            )

        # Stage 4: Hallucination Detection
        if not package or not package.hallucination_report:
            script_to_validate = self._script_to_powershell(initial_script)
            package_logger.log_5_stage_pipeline(
                4,
                "Hallucination Detection",
                "START",
                {"script_to_validate_length": len(script_to_validate)},
            )
            with PIPELINE_STAGE_SECONDS.labels("hallucination_detection").time():
                hallucination_report = self.hallucination_detector.detect(
                    script_to_validate
                )
            if package and session:
                package.hallucination_report = hallucination_report
                package.current_step = "hallucination_detection"
                package.progress_pct = pct("hallucination_detection")
                session.commit()
                if progress_queue:
                    progress_queue.put(
                        {
                            "status": "processing",
                            "progress": package.progress_pct,
                            "current_step": "Hallucination Detection",
                            "stage_number": 4,
                        }
                    )
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "hallucination_detection",
                    pct("hallucination_detection"),
                )
            package_logger.log_5_stage_pipeline(
                4,
                "Hallucination Detection",
                "COMPLETED",
                {"hallucination_report": hallucination_report},
            )
        else:
            hallucination_report = package.hallucination_report if package else {}

        # Stage 5: Advisor AI
        if hallucination_report.get("has_hallucinations", False):
            if not package or not package.generated_script:
                package_logger.log_5_stage_pipeline(
                    5,
                    "Advisor AI",
                    "START",
                    {"hallucination_report": hallucination_report},
                )
                with PIPELINE_STAGE_SECONDS.labels("advisor_correction").time():
                    corrected_script = self.advisor_service.correct_script(
                        initial_script, hallucination_report, package_id
                    )
                if package and session:
                    package.generated_script = corrected_script.model_dump()
                    package.current_step = "advisor_correction"
                    package.progress_pct = pct("advisor_correction")
                    session.commit()
                    if progress_queue:
                        progress_queue.put(
                            {
                                "status": "processing",
                                "progress": package.progress_pct,
                                "current_step": "Advisor AI",
                                "stage_number": 5,
                            }
                        )
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "advisor_correction",
                    pct("advisor_correction"),
                )
                corrected_script.hallucination_report = hallucination_report
                package_logger.log_5_stage_pipeline(
                    5,
                    "Advisor AI",
                    "COMPLETED",
                    {"corrected_script": corrected_script.model_dump()},
                )
                return corrected_script
            else:
                return (
                    PSADTScript(**package.generated_script)
                    if package and package.generated_script
                    else initial_script
                )
        else:
            initial_script.hallucination_report = hallucination_report
            if package and session:
                package.generated_script = initial_script.model_dump()
                package.progress_pct = pct("hallucination_detection")
                session.commit()
            package_logger.log_5_stage_pipeline(
                5, "Advisor AI", "SKIPPED", {"reason": "No hallucinations detected"}
            )
            return initial_script

    def _generate_initial_script(
        self,
        instruction_result: InstructionResult,
        documentation: str,
        package: Package | None,
    ) -> PSADTScript:
        """Generate initial PSADT script based on instructions and documentation."""
        from .instruction_processor import InstructionProcessor
        import json

        ip = InstructionProcessor()

        prompt = ip.jinja_env.get_template("script_generation.j2").render(
            instructions=instruction_result.structured_instructions,
            documentation=documentation,
            package=package,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an expert PowerShell developer specializing in the PSAppDeployToolkit. Return a valid JSON object matching the PSADTScript schema.",
            },
            {"role": "user", "content": prompt},
        ]

        response = ip.client.chat.completions.create(
            model=Config.AI_MODEL,  # Use Config.AI_MODEL
            messages=messages,
            response_format={"type": "json_object"},
        )

        response_content = response.choices[0].message.content or "{}"
        script_data = json.loads(response_content)

        return PSADTScript(**script_data)

    def _script_to_powershell(self, script: PSADTScript) -> str:
        """Convert PSADTScript object to PowerShell script string for validation."""
        sections = []

        if script.pre_installation_tasks:
            sections.append("# Pre-Installation Tasks")
            sections.extend(script.pre_installation_tasks)
            sections.append("")

        if script.installation_tasks:
            sections.append("# Installation Tasks")
            sections.extend(script.installation_tasks)
            sections.append("")

        if script.post_installation_tasks:
            sections.append("# Post-Installation Tasks")
            sections.extend(script.post_installation_tasks)
            sections.append("")

        if script.uninstallation_tasks:
            sections.append("# Uninstallation Tasks")
            sections.extend(script.uninstallation_tasks)
            sections.append("")

        if script.post_uninstallation_tasks:
            sections.append("# Post-Uninstallation Tasks")
            sections.extend(script.post_uninstallation_tasks)
            sections.append("")

        if script.pre_repair_tasks:
            sections.append("# Pre-Repair Tasks")
            sections.extend(script.pre_repair_tasks)
            sections.append("")

        if script.repair_tasks:
            sections.append("# Repair Tasks")
            sections.extend(script.repair_tasks)
            sections.append("")

        if script.post_repair_tasks:
            sections.append("# Post-Repair Tasks")
            sections.extend(script.post_repair_tasks)

        return "\n".join(sections)

    def resume_incomplete_jobs(self, session: Session) -> None:
        """
        Resumes all incomplete jobs.
        """
        incomplete_packages = (
            session.query(Package).filter(Package.status == "processing").all()
        )
        for package in incomplete_packages:
            self.generate_script(
                package.custom_instructions or "", package=package, session=session
            )
