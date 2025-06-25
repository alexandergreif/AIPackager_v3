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


class PSADTGenerator:
    def __init__(self) -> None:
        self.instruction_processor = InstructionProcessor()
        self.rag_service = RAGService()
        self.hallucination_detector = HallucinationDetector()
        self.advisor_service = AdvisorService()

    @retry_with_backoff()
    def generate_script(self, text: str) -> PSADTScript:
        """
        5-stage pipeline for generating validated PSADT scripts.
        """
        # Stage 1: Instruction Processing
        instruction_result = self.instruction_processor.process_instructions(text)

        # Stage 2: Targeted RAG - Query documentation for predicted cmdlets
        rag_documentation = self.rag_service.query(instruction_result.predicted_cmdlets)

        # Stage 3: Script Generation - Generate initial script with documentation
        initial_script = self._generate_initial_script(
            instruction_result, rag_documentation
        )

        # Stage 4: Hallucination Detection - Validate the generated script
        hallucination_report = self.hallucination_detector.detect(
            self._script_to_powershell(initial_script)
        )

        # Stage 5: Advisor AI - Apply corrections if hallucinations detected
        if hallucination_report.get("has_hallucinations", False):
            corrected_script = self.advisor_service.correct_script(
                initial_script, hallucination_report
            )
            corrected_script.hallucination_report = hallucination_report
            return corrected_script
        else:
            initial_script.hallucination_report = hallucination_report
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
