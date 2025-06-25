"""ScriptRenderer for PSADT script generation and prompt template rendering."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from jinja2 import Environment, FileSystemLoader, TemplateSyntaxError

from .models import Package, Metadata

logger = logging.getLogger(__name__)


class ScriptRenderer:
    """Renders PSADT scripts and AI prompt templates using Jinja2."""

    def __init__(self) -> None:
        """Initialize the ScriptRenderer with template environments."""
        self._prompt_env: Optional[Environment] = None
        self._psadt_env: Optional[Environment] = None

    @property
    def prompt_env(self) -> Environment:
        """Get or create the prompt template environment."""
        if self._prompt_env is None:
            prompts_dir = Path("src/app/prompts")
            if not prompts_dir.exists():
                raise FileNotFoundError(f"Prompts directory not found: {prompts_dir}")

            self._prompt_env = Environment(
                loader=FileSystemLoader(str(prompts_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return self._prompt_env

    @property
    def psadt_env(self) -> Environment:
        """Get or create the PSADT template environment."""
        if self._psadt_env is None:
            templates_dir = Path("src/app/templates")
            if not templates_dir.exists():
                raise FileNotFoundError(
                    f"Templates directory not found: {templates_dir}"
                )

            self._psadt_env = Environment(
                loader=FileSystemLoader(str(templates_dir)),
                trim_blocks=True,
                lstrip_blocks=True,
            )
        return self._psadt_env

    def render_psadt_script(self, package: Package, ai_sections: Dict[str, str]) -> str:
        """Render the complete PSADT script using the template and AI-generated sections.

        Args:
            package: Package object with metadata
            ai_sections: Dictionary containing AI-generated script sections

        Returns:
            Rendered PowerShell script as string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            FileNotFoundError: If template file is not found
        """
        try:
            # Get template context
            context = self.get_template_context(package, package.package_metadata)

            # Add AI-generated sections to context
            context.update(
                {
                    "pre_installation_tasks": ai_sections.get(
                        "pre_installation_tasks",
                        "# No pre-installation tasks specified",
                    ),
                    "installation_tasks": ai_sections.get(
                        "installation_tasks", "# No installation tasks specified"
                    ),
                    "post_installation_tasks": ai_sections.get(
                        "post_installation_tasks",
                        "# No post-installation tasks specified",
                    ),
                    "uninstallation_tasks": ai_sections.get(
                        "uninstallation_tasks", "# No uninstallation tasks specified"
                    ),
                    "post_uninstallation_tasks": ai_sections.get(
                        "post_uninstallation_tasks",
                        "# No post-uninstallation tasks specified",
                    ),
                    "pre_repair_tasks": ai_sections.get(
                        "pre_repair_tasks", "# No pre-repair tasks specified"
                    ),
                    "repair_tasks": ai_sections.get(
                        "repair_tasks", "# No repair tasks specified"
                    ),
                    "post_repair_tasks": ai_sections.get(
                        "post_repair_tasks", "# No post-repair tasks specified"
                    ),
                }
            )

            # Load and render the PSADT template
            template = self.psadt_env.get_template(
                "psadt/Invoke-AppDeployToolkit.ps1.j2"
            )
            rendered_script: str = template.render(context)

            logger.info(f"Successfully rendered PSADT script for package {package.id}")
            return rendered_script

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in PSADT template: {e}")
            raise
        except Exception as e:
            logger.error(f"Error rendering PSADT script for package {package.id}: {e}")
            raise

    def render_prompt_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> str:
        """Render an AI prompt template with the given context.

        Args:
            template_name: Name of the template file (e.g., "system.j2")
            context: Dictionary containing template variables

        Returns:
            Rendered prompt as string

        Raises:
            TemplateSyntaxError: If template has syntax errors
            FileNotFoundError: If template file is not found
        """
        try:
            template = self.prompt_env.get_template(template_name)
            rendered_prompt: str = template.render(context)

            logger.debug(f"Successfully rendered prompt template: {template_name}")
            return rendered_prompt

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error rendering prompt template {template_name}: {e}")
            raise

    def get_template_context(
        self, package: Package, metadata: Optional[Metadata]
    ) -> Dict[str, Any]:
        """Build template context dictionary from package and metadata.

        Args:
            package: Package object
            metadata: Metadata object (can be None)

        Returns:
            Dictionary containing all template variables
        """
        # Base context with fallback values
        context = {
            "app_name": "Unknown Application",
            "app_version": "1.0.0",
            "app_vendor": "Unknown Publisher",
            "app_arch": "x64",
            "app_lang": "EN",
            "app_revision": "01",
            "app_script_date": datetime.now().strftime("%Y-%m-%d"),
            "app_script_author": "AIPackager v3",
            "product_code": "",
            "upgrade_code": "",
        }

        # Update with metadata if available
        if metadata:
            context.update(
                {
                    "app_name": metadata.product_name or context["app_name"],
                    "app_version": metadata.version or context["app_version"],
                    "app_vendor": metadata.publisher or context["app_vendor"],
                    "app_arch": metadata.architecture or context["app_arch"],
                    "product_code": metadata.product_code or "",
                    "upgrade_code": metadata.upgrade_code or "",
                }
            )

        # Add package information
        context.update(
            {
                "package_filename": package.filename,
                "custom_instructions": package.custom_instructions or "",
            }
        )

        # Determine file extension for template logic
        if package.filename:
            file_ext = Path(package.filename).suffix.lower()
            context["file_extension"] = file_ext.lstrip(".")
        else:
            context["file_extension"] = "msi"

        return context

    def validate_template_syntax(self, template_name: str) -> bool:
        """Validate that a template has correct Jinja2 syntax.

        Args:
            template_name: Name of the template to validate

        Returns:
            True if template syntax is valid, False otherwise
        """
        try:
            # Try to load the template
            if template_name.endswith(".j2"):
                # Prompt template
                template = self.prompt_env.get_template(template_name)
            else:
                # PSADT template
                template = self.psadt_env.get_template(template_name)

            # Try to render with empty context to check syntax
            template.render({})
            return True

        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error in {template_name}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error validating template {template_name}: {e}")
            return False

    def list_available_templates(self) -> Dict[str, list]:
        """List all available templates.

        Returns:
            Dictionary with 'prompt_templates' and 'psadt_templates' lists
        """
        result: Dict[str, list] = {"prompt_templates": [], "psadt_templates": []}

        try:
            # List prompt templates
            prompts_dir = Path("src/app/prompts")
            if prompts_dir.exists():
                result["prompt_templates"] = [f.name for f in prompts_dir.glob("*.j2")]

            # List PSADT templates
            psadt_dir = Path("src/app/templates/psadt")
            if psadt_dir.exists():
                result["psadt_templates"] = [
                    f"psadt/{f.name}" for f in psadt_dir.glob("*.j2")
                ]

        except Exception as e:
            logger.error(f"Error listing templates: {e}")

        return result
