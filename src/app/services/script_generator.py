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
from typing import ContextManager

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
    ) -> PSADTScript:
        """
        5-stage pipeline for generating validated PSADT scripts.
        """
        # Stage 1: Instruction Processing
        with PIPELINE_STAGE_SECONDS.labels("instruction_processing").time():
            instruction_result = self.instruction_processor.process_instructions(text)
        if package and session:
            package.current_step = "instruction_processing"
            package.progress_pct = pct("instruction_processing")
            session.commit()
            logger_cm.info(
                "Stage %s \u2192 %s %%",
                "instruction_processing",
                pct("instruction_processing"),
            )

        # Stage 2: Targeted RAG - Query documentation for predicted cmdlets
        with PIPELINE_STAGE_SECONDS.labels("rag_enrichment").time():
            rag_documentation = self.rag_service.query(
                instruction_result.predicted_cmdlets
            )
        if package and session:
            package.current_step = "rag_enrichment"
            package.progress_pct = pct("rag_enrichment")
            session.commit()
            logger_cm.info(
                "Stage %s \u2192 %s %%",
                "rag_enrichment",
                pct("rag_enrichment"),
            )

        # Stage 3: Script Generation - Generate initial script with documentation
        with PIPELINE_STAGE_SECONDS.labels("script_generation").time():
            initial_script = self._generate_initial_script(
                instruction_result, rag_documentation
            )
        if package and session:
            package.current_step = "script_generation"
            package.progress_pct = pct("script_generation")
            session.commit()
            logger_cm.info(
                "Stage %s \u2192 %s %%",
                "script_generation",
                pct("script_generation"),
            )

        # Stage 4: Hallucination Detection - Validate the generated script
        with PIPELINE_STAGE_SECONDS.labels("hallucination_detection").time():
            hallucination_report = self.hallucination_detector.detect(
                self._script_to_powershell(initial_script)
            )
        if package and session:
            package.current_step = "hallucination_detection"
            package.progress_pct = pct("hallucination_detection")
            session.commit()
            logger_cm.info(
                "Stage %s \u2192 %s %%",
                "hallucination_detection",
                pct("hallucination_detection"),
            )

        # Stage 5: Advisor AI - Apply corrections if hallucinations detected
        if hallucination_report.get("has_hallucinations", False):
            with PIPELINE_STAGE_SECONDS.labels("advisor_correction").time():
                corrected_script = self.advisor_service.correct_script(
                    initial_script, hallucination_report
                )
            if package and session:
                package.current_step = "advisor_correction"
                package.progress_pct = pct("advisor_correction")
                session.commit()
                logger_cm.info(
                    "Stage %s \u2192 %s %%",
                    "advisor_correction",
                    pct("advisor_correction"),
                )
            corrected_script.hallucination_report = hallucination_report
            return corrected_script
        else:
            initial_script.hallucination_report = hallucination_report
            if package and session:
                package.progress_pct = pct("hallucination_detection")
            return initial_script

    def _generate_initial_script(
        self, instruction_result: InstructionResult, documentation: str
    ) -> PSADTScript:
        """Generate initial PSADT script based on instructions and documentation."""
        # For now, use a working mock implementation since the template expects metadata
        # that we don't have in this context. In a full implementation, this would
        # call OpenAI with the script_generation.j2 template

        user_instructions = instruction_result.structured_instructions.get(
            "user_instructions", "Install the application"
        )
        installer_name = instruction_result.structured_instructions.get(
            "installer_name", "setup.msi"
        )

        return PSADTScript(
            pre_installation_tasks=[
                "Show-ADTInstallationWelcome -CloseAppsCountdown 60 -CheckDiskSpace",
                "Get-ADTLoggedOnUser",
                "Test-ADTCallerIsAdmin",
                f"Write-ADTLogEntry -Message 'Starting installation based on: {user_instructions}' -Severity 1",
            ],
            installation_tasks=[
                "Write-ADTLogEntry -Message 'Beginning installation process' -Severity 1",
                f"Start-ADTMsiProcess -Action Install -Path '$dirFiles\\{installer_name}'",
                "Write-ADTLogEntry -Message 'Installation completed successfully' -Severity 1",
            ],
            post_installation_tasks=[
                "Show-ADTInstallationProgress -StatusMessage 'Finalizing installation...'",
                "Write-ADTLogEntry -Message 'Running post-installation tasks' -Severity 1",
                "Set-ADTRegistryKey -Key 'HKLM:\\SOFTWARE\\Company\\Product' -Name 'InstallDate' -Value (Get-Date -Format 'yyyy-MM-dd')",
            ],
            uninstallation_tasks=[
                "Write-ADTLogEntry -Message 'Beginning uninstallation process' -Severity 1",
                f"Start-ADTMsiProcess -Action Uninstall -Path '$dirFiles\\{installer_name}'",
                "Write-ADTLogEntry -Message 'Uninstallation completed successfully' -Severity 1",
            ],
            post_uninstallation_tasks=[
                "Write-ADTLogEntry -Message 'Running post-uninstallation cleanup' -Severity 1",
                "Remove-ADTRegistryKey -Key 'HKLM:\\SOFTWARE\\Company\\Product'",
                "Remove-ADTFolder -Path '$envProgramFiles\\Company\\Product' -ContinueOnError $true",
            ],
        )

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

        return "\n".join(sections)
