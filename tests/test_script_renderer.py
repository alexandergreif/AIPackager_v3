"""Tests for SP3-03: ScriptRenderer class for PSADT script generation."""

import pytest
from unittest.mock import Mock
from pathlib import Path

from src.app.script_renderer import ScriptRenderer
from src.app.models import Package, Metadata


class TestScriptRenderer:
    """Test cases for ScriptRenderer class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.renderer = ScriptRenderer()

        # Mock package data
        self.mock_package = Mock(spec=Package)
        self.mock_package.id = "test-package-id"
        self.mock_package.filename = "test-app.msi"
        self.mock_package.custom_instructions = "Install silently with custom settings"

        # Mock metadata
        self.mock_metadata = Mock(spec=Metadata)
        self.mock_metadata.product_name = "Test Application"
        self.mock_metadata.version = "1.0.0"
        self.mock_metadata.publisher = "Test Publisher"
        self.mock_metadata.architecture = "x64"
        self.mock_metadata.product_code = "{12345678-1234-1234-1234-123456789012}"

        self.mock_package.package_metadata = self.mock_metadata

    def test_script_renderer_initialization(self):
        """Test that ScriptRenderer can be initialized."""
        renderer = ScriptRenderer()
        assert renderer is not None

    def test_render_psadt_script_with_mock_data(self):
        """Test rendering PSADT script with mock AI-generated sections."""
        # Mock AI-generated content sections
        ai_sections = {
            "pre_installation_tasks": "Write-ADTLogEntry -Message 'Starting pre-installation tasks'",
            "installation_tasks": "Start-ADTMsiProcess -Path '$dirFiles\\test-app.msi' -Parameters '/quiet'",
            "post_installation_tasks": "Write-ADTLogEntry -Message 'Installation completed successfully'",
            "uninstallation_tasks": "Start-ADTMsiProcess -Action 'Uninstall' -Path '$productCode'",
            "post_uninstallation_tasks": "Write-ADTLogEntry -Message 'Uninstallation completed'",
        }

        # This should fail initially since ScriptRenderer doesn't exist yet
        rendered_script = self.renderer.render_psadt_script(
            self.mock_package, ai_sections
        )

        # Verify the rendered script contains expected elements
        assert "Test Application" in rendered_script
        assert "1.0.0" in rendered_script
        assert "Test Publisher" in rendered_script
        assert "x64" in rendered_script
        assert "Starting pre-installation tasks" in rendered_script
        assert "Start-ADTMsiProcess" in rendered_script
        assert "Installation completed successfully" in rendered_script

    def test_render_psadt_script_handles_missing_metadata(self):
        """Test that renderer handles packages with missing metadata gracefully."""
        package_no_metadata = Mock(spec=Package)
        package_no_metadata.package_metadata = None
        package_no_metadata.filename = "unknown-app.exe"

        ai_sections = {
            "installation_tasks": "Start-ADTProcess -Path '$dirFiles\\unknown-app.exe' -Parameters '/S'"
        }

        # Should not raise an exception
        rendered_script = self.renderer.render_psadt_script(
            package_no_metadata, ai_sections
        )
        assert "unknown-app.exe" in rendered_script

    def test_render_prompt_template_system_prompt(self):
        """Test rendering system prompt template for AI interactions."""
        context = {
            "role": "PSADT expert",
            "guidelines": "Use only PSADT cmdlets, follow CMTrace logging format",
        }

        # This should fail initially since the method doesn't exist yet
        rendered_prompt = self.renderer.render_prompt_template("system.j2", context)

        assert "PSADT" in rendered_prompt
        assert "expert" in rendered_prompt
        assert "CMTrace logging format" in rendered_prompt

    def test_render_prompt_template_instruction_processing(self):
        """Test rendering instruction processing prompt template."""
        context = {
            "user_instructions": "Install VLC media player silently",
            "metadata": {
                "product_name": "VLC media player",
                "version": "3.0.18",
                "file_type": "exe",
            },
        }

        rendered_prompt = self.renderer.render_prompt_template(
            "instruction_processing.j2", context
        )

        assert "VLC media player" in rendered_prompt
        assert "Install" in rendered_prompt
        assert "silently" in rendered_prompt

    def test_render_prompt_template_script_generation(self):
        """Test rendering script generation prompt template."""
        context = {
            "structured_instructions": {
                "action": "install",
                "silent": True,
                "predicted_cmdlets": [
                    "Start-ADTProcess",
                    "Show-ADTInstallationWelcome",
                ],
            },
            "rag_documentation": "Start-ADTProcess documentation: Use -Path parameter for executable path...",
            "metadata": self.mock_metadata.__dict__,
        }

        rendered_prompt = self.renderer.render_prompt_template(
            "script_generation.j2", context
        )

        assert "Start-ADTProcess" in rendered_prompt
        assert "Show-ADTInstallationWelcome" in rendered_prompt
        assert "Test Application" in rendered_prompt

    def test_render_prompt_template_advisor_correction(self):
        """Test rendering advisor correction prompt template."""
        context = {
            "original_script": "Start-InvalidCmdlet -Path 'test.exe'",
            "hallucination_report": {
                "invalid_cmdlets": ["Start-InvalidCmdlet"],
                "suggested_fixes": ["Use Start-ADTProcess instead"],
            },
            "rag_corrections": "Start-ADTProcess is the correct PSADT cmdlet for launching processes...",
        }

        rendered_prompt = self.renderer.render_prompt_template(
            "advisor_correction.j2", context
        )

        assert "Start-InvalidCmdlet" in rendered_prompt
        assert "Start-ADTProcess" in rendered_prompt
        assert "hallucination" in rendered_prompt.lower()

    def test_get_template_context_builds_proper_context(self):
        """Test that get_template_context builds proper context dictionary."""
        context = self.renderer.get_template_context(
            self.mock_package, self.mock_metadata
        )

        # Should include all necessary template variables
        assert context["app_name"] == "Test Application"
        assert context["app_version"] == "1.0.0"
        assert context["app_vendor"] == "Test Publisher"
        assert context["app_arch"] == "x64"
        assert context["product_code"] == "{12345678-1234-1234-1234-123456789012}"
        assert "app_script_date" in context
        assert "app_script_author" in context

    def test_get_template_context_handles_none_metadata(self):
        """Test that get_template_context handles None metadata gracefully."""
        context = self.renderer.get_template_context(self.mock_package, None)

        # Should provide fallback values
        assert context["app_name"] == "Unknown Application"
        assert context["app_version"] == "1.0.0"
        assert context["app_vendor"] == "Unknown Publisher"

    def test_rendered_script_is_valid_powershell_syntax(self):
        """Test that rendered script has valid PowerShell syntax structure."""
        ai_sections = {
            "installation_tasks": "Start-ADTMsiProcess -Path '$dirFiles\\test.msi'"
        }

        rendered_script = self.renderer.render_psadt_script(
            self.mock_package, ai_sections
        )

        # Check for basic PowerShell script structure
        assert "[CmdletBinding()]" in rendered_script
        assert "param" in rendered_script
        assert "function Install-ADTDeployment" in rendered_script
        assert "function Uninstall-ADTDeployment" in rendered_script
        assert "$adtSession = @{" in rendered_script
        assert "Import-Module" in rendered_script

    def test_template_variables_are_properly_escaped(self):
        """Test that template variables are properly escaped for PowerShell."""
        # Test with potentially problematic characters
        self.mock_metadata.product_name = "Test App with 'Quotes' & Symbols"

        ai_sections = {"installation_tasks": "Write-ADTLogEntry -Message 'Installing'"}

        rendered_script = self.renderer.render_psadt_script(
            self.mock_package, ai_sections
        )

        # Should handle special characters properly
        assert "Test App with" in rendered_script
        # Should not break PowerShell syntax
        assert rendered_script.count("'") % 2 == 0  # Quotes should be balanced


class TestPromptTemplates:
    """Test cases for prompt template files."""

    def test_prompt_templates_directory_exists(self):
        """Test that prompt templates directory exists."""
        prompts_dir = Path("src/app/prompts")
        assert prompts_dir.exists()

    def test_required_prompt_templates_exist(self):
        """Test that all required prompt template files exist."""
        prompts_dir = Path("src/app/prompts")
        required_templates = [
            "system.j2",
            "user.j2",
            "instruction_processing.j2",
            "targeted_rag_context.j2",
            "script_generation.j2",
            "advisor_correction.j2",
        ]

        for template in required_templates:
            template_path = prompts_dir / template
            assert template_path.exists(), f"Template {template} should exist"

    def test_prompt_templates_are_valid_jinja2(self):
        """Test that prompt templates contain valid Jinja2 syntax."""
        from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

        prompts_dir = Path("src/app/prompts")
        env = Environment(loader=FileSystemLoader(str(prompts_dir)))

        # Minimal context for templates that require variables
        minimal_context = {
            "metadata": {
                "product_name": "Test App",
                "version": "1.0.0",
                "file_type": "msi",
            },
            "user_instructions": "Test instructions",
            "structured_instructions": {"action": "install"},
            "rag_documentation": "Test documentation",
            "original_script": "Test script",
            "hallucination_report": {"invalid_cmdlets": []},
            "rag_corrections": "Test corrections",
            "predicted_cmdlets": ["Start-ADTProcess"],
        }

        templates = [
            "system.j2",
            "instruction_processing.j2",
            "script_generation.j2",
            "advisor_correction.j2",
        ]

        for template_name in templates:
            try:
                template = env.get_template(template_name)
                # Try to render with minimal context to check syntax
                template.render(minimal_context)
            except TemplateSyntaxError as e:
                pytest.fail(f"Template {template_name} has invalid Jinja2 syntax: {e}")
