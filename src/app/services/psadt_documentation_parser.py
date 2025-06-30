"""
PSADT v4 Documentation Parser

Parses PSADT v4 MDX documentation files to extract complete cmdlet specifications
including parameters, types, valid values, and parameter sets.
"""

import re
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ParameterType(Enum):
    STRING = "String"
    INT32 = "Int32"
    UINT32 = "UInt32"
    BOOLEAN = "Boolean"
    SWITCH = "SwitchParameter"
    STRING_ARRAY = "String[]"
    INT32_ARRAY = "Int32[]"
    GUID = "Guid"
    PROCESS_OBJECT_ARRAY = "ProcessObject[]"
    INSTALLED_APPLICATION = "InstalledApplication"
    DEPLOYMENT_TYPE = "DeploymentType"
    PROCESS_PRIORITY_CLASS = "ProcessPriorityClass"


@dataclass
class ParameterDefinition:
    """Definition of a single parameter"""

    name: str
    type: ParameterType
    mandatory: bool = False
    position: Optional[int] = None
    default_value: Optional[str] = None
    valid_values: List[str] = field(default_factory=list)
    description: str = ""
    aliases: List[str] = field(default_factory=list)
    pipeline_input: bool = False
    wildcard_characters: bool = False


@dataclass
class ParameterSet:
    """Definition of a parameter set"""

    name: str
    required_parameters: Set[str] = field(default_factory=set)
    optional_parameters: Set[str] = field(default_factory=set)
    description: str = ""


@dataclass
class CmdletExample:
    """Example usage of a cmdlet"""

    title: str
    code: str
    description: str


@dataclass
class CmdletDefinition:
    """Complete definition of a PSADT v4 cmdlet"""

    name: str
    synopsis: str = ""
    description: str = ""
    parameters: Dict[str, ParameterDefinition] = field(default_factory=dict)
    parameter_sets: Dict[str, ParameterSet] = field(default_factory=dict)
    examples: List[CmdletExample] = field(default_factory=list)
    notes: str = ""
    related_links: List[str] = field(default_factory=list)
    inputs: str = ""
    outputs: str = ""
    common_parameters: bool = True


class PSADTDocumentationParser:
    """Parser for PSADT v4 MDX documentation files"""

    def __init__(self, docs_path: str = "PSADT/docs/docs"):
        self.docs_path = Path(docs_path)
        self.cmdlets: Dict[str, CmdletDefinition] = {}

    def parse_all_cmdlets(self) -> Dict[str, CmdletDefinition]:
        """Parse all MDX files and extract cmdlet definitions"""
        logger.info(f"Parsing PSADT v4 documentation from {self.docs_path}")

        if not self.docs_path.exists():
            logger.error(f"Documentation path does not exist: {self.docs_path}")
            return {}

        mdx_files = list(self.docs_path.glob("*.mdx"))
        logger.info(f"Found {len(mdx_files)} MDX files to parse")

        for mdx_file in mdx_files:
            try:
                cmdlet_def = self.parse_mdx_file(mdx_file)
                if cmdlet_def:
                    self.cmdlets[cmdlet_def.name] = cmdlet_def
                    logger.debug(f"Parsed cmdlet: {cmdlet_def.name}")
            except Exception as e:
                logger.error(f"Error parsing {mdx_file}: {e}")
                continue

        logger.info(f"Successfully parsed {len(self.cmdlets)} cmdlets")
        return self.cmdlets

    def parse_mdx_file(self, file_path: Path) -> Optional[CmdletDefinition]:
        """Parse a single MDX file to extract cmdlet definition"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            logger.error(f"Could not read file {file_path}: {e}")
            return None

        # Extract cmdlet name from frontmatter
        cmdlet_name = self._extract_cmdlet_name(content, file_path.stem)
        if not cmdlet_name:
            logger.warning(f"Could not extract cmdlet name from {file_path}")
            return None

        cmdlet_def = CmdletDefinition(name=cmdlet_name)

        # Parse each section
        cmdlet_def.synopsis = self._extract_synopsis(content)
        cmdlet_def.description = self._extract_description(content)

        # Parse syntax to identify parameter sets
        cmdlet_def.parameter_sets = self._extract_parameter_sets(content, cmdlet_name)

        # Parse parameters section
        cmdlet_def.parameters = self._extract_parameters(content)

        # Parse examples
        cmdlet_def.examples = self._extract_examples(content)

        # Parse additional sections
        cmdlet_def.notes = self._extract_notes(content)
        cmdlet_def.inputs = self._extract_inputs(content)
        cmdlet_def.outputs = self._extract_outputs(content)
        cmdlet_def.related_links = self._extract_related_links(content)

        return cmdlet_def

    def _extract_cmdlet_name(self, content: str, filename: str) -> Optional[str]:
        """Extract cmdlet name from frontmatter or filename"""
        # Try frontmatter first
        frontmatter_match = re.search(r"id:\s*(\S+)", content)
        if frontmatter_match:
            return frontmatter_match.group(1)

        # Try title in frontmatter
        title_match = re.search(r"title:\s*(\S+)", content)
        if title_match:
            return title_match.group(1)

        # Fallback to filename
        return (
            filename
            if filename.startswith(
                (
                    "Add-",
                    "Block-",
                    "Close-",
                    "Complete-",
                    "Convert-",
                    "Copy-",
                    "Disable-",
                    "Dismount-",
                    "Enable-",
                    "Export-",
                    "Get-",
                    "Initialize-",
                    "Install-",
                    "Invoke-",
                    "Mount-",
                    "New-",
                    "Open-",
                    "Out-",
                    "Register-",
                    "Remove-",
                    "Reset-",
                    "Resolve-",
                    "Send-",
                    "Set-",
                    "Show-",
                    "Start-",
                    "Stop-",
                )
            )
            else None
        )

    def _extract_synopsis(self, content: str) -> str:
        """Extract synopsis section"""
        match = re.search(
            r"## SYNOPSIS\s*\n\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        return match.group(1).strip() if match else ""

    def _extract_description(self, content: str) -> str:
        """Extract description section"""
        match = re.search(
            r"## DESCRIPTION\s*\n\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        return match.group(1).strip() if match else ""

    def _extract_parameter_sets(
        self, content: str, cmdlet_name: str
    ) -> Dict[str, ParameterSet]:
        """Extract parameter sets from syntax section"""
        parameter_sets: Dict[str, Any] = {}

        # Find syntax section
        syntax_match = re.search(
            r"## SYNTAX\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        if not syntax_match:
            return parameter_sets

        syntax_content = syntax_match.group(1)

        # Find parameter set headers
        set_pattern = r"### (\w+)(?: \(Default\))?\s*\n\n```powershell\s*\n(.*?)\n```"

        for match in re.finditer(set_pattern, syntax_content, re.DOTALL):
            set_name = match.group(1)
            syntax_line = match.group(2).strip()

            # Parse the PowerShell syntax line
            param_set = self._parse_syntax_line(syntax_line, cmdlet_name)
            param_set.name = set_name
            parameter_sets[set_name] = param_set

        # If no named parameter sets found, create a default one
        if not parameter_sets:
            powershell_blocks = re.findall(
                r"```powershell\s*\n(.*?)\n```", syntax_content, re.DOTALL
            )
            if powershell_blocks:
                param_set = self._parse_syntax_line(
                    powershell_blocks[0].strip(), cmdlet_name
                )
                param_set.name = "Default"
                parameter_sets["Default"] = param_set

        return parameter_sets

    def _parse_syntax_line(self, syntax_line: str, cmdlet_name: str) -> ParameterSet:
        """Parse a PowerShell syntax line to extract parameter information"""
        param_set = ParameterSet(name="")

        # Remove the cmdlet name from the beginning
        if syntax_line.startswith(cmdlet_name):
            syntax_line = syntax_line[len(cmdlet_name) :].strip()

        # Find all parameters in the syntax
        # Pattern for parameters: [-ParameterName <Type>] or [-ParameterName]
        param_pattern = r"\[?-(\w+)(?:\s+<([^>]+)>)?\]?"

        for match in re.finditer(param_pattern, syntax_line):
            param_name = match.group(1)
            # param_type = match.group(2)  # Currently not used

            # Determine if parameter is required or optional based on brackets
            param_context = syntax_line[max(0, match.start() - 5) : match.end() + 5]
            is_optional = (
                "[" in param_context
                or syntax_line[match.start() - 1 : match.start()] == "["
            )

            if is_optional:
                param_set.optional_parameters.add(param_name)
            else:
                param_set.required_parameters.add(param_name)

        return param_set

    def _extract_parameters(self, content: str) -> Dict[str, ParameterDefinition]:
        """Extract parameter definitions from parameters section"""
        parameters: dict[str, ParameterDefinition] = {}

        # Find parameters section
        params_match = re.search(
            r"## PARAMETERS\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        if not params_match:
            return parameters

        params_content = params_match.group(1)

        # Find each parameter definition
        param_pattern = r"### -(\w+)\s*\n\n(.*?)(?=\n### -|\n## |\Z)"

        for match in re.finditer(param_pattern, params_content, re.DOTALL):
            param_name = match.group(1)
            param_content = match.group(2).strip()

            param_def = self._parse_parameter_definition(param_name, param_content)
            parameters[param_name] = param_def

        return parameters

    def _parse_parameter_definition(
        self, param_name: str, param_content: str
    ) -> ParameterDefinition:
        """Parse a single parameter definition"""
        param_def = ParameterDefinition(name=param_name, type=ParameterType.STRING)

        # Extract description (first paragraph)
        desc_match = re.search(r"^(.*?)(?=\n\n|\n```|\Z)", param_content, re.DOTALL)
        if desc_match:
            param_def.description = desc_match.group(1).strip()

        # Find YAML block with parameter details
        yaml_match = re.search(r"```yaml\s*\n(.*?)\n```", param_content, re.DOTALL)
        if yaml_match:
            yaml_content = yaml_match.group(1)

            # Parse YAML-like content
            type_match = re.search(r"Type:\s*(\S+)", yaml_content)
            if type_match:
                type_str = type_match.group(1)
                param_def.type = self._parse_parameter_type(type_str)

            # Check if required
            required_match = re.search(r"Required:\s*(True|False)", yaml_content)
            if required_match:
                param_def.mandatory = required_match.group(1) == "True"

            # Get default value
            default_match = re.search(r"Default value:\s*(.+)", yaml_content)
            if default_match:
                default_val = default_match.group(1).strip()
                if default_val and default_val != "None":
                    param_def.default_value = default_val

            # Check for valid values (enum)
            accepted_match = re.search(r"Accepted values:\s*(.+)", yaml_content)
            if accepted_match:
                values_str = accepted_match.group(1)
                param_def.valid_values = [v.strip() for v in values_str.split(",")]

            # Check pipeline input
            pipeline_match = re.search(
                r"Accept pipeline input:\s*(True|False)", yaml_content
            )
            if pipeline_match:
                param_def.pipeline_input = pipeline_match.group(1) == "True"

        return param_def

    def _parse_parameter_type(self, type_str: str) -> ParameterType:
        """Parse parameter type string to enum"""
        type_mapping = {
            "String": ParameterType.STRING,
            "Int32": ParameterType.INT32,
            "UInt32": ParameterType.UINT32,
            "Boolean": ParameterType.BOOLEAN,
            "SwitchParameter": ParameterType.SWITCH,
            "String[]": ParameterType.STRING_ARRAY,
            "Int32[]": ParameterType.INT32_ARRAY,
            "Guid": ParameterType.GUID,
            "ProcessObject[]": ParameterType.PROCESS_OBJECT_ARRAY,
            "InstalledApplication": ParameterType.INSTALLED_APPLICATION,
            "DeploymentType": ParameterType.DEPLOYMENT_TYPE,
            "ProcessPriorityClass": ParameterType.PROCESS_PRIORITY_CLASS,
        }

        return type_mapping.get(type_str, ParameterType.STRING)

    def _extract_examples(self, content: str) -> List[CmdletExample]:
        """Extract examples section"""
        examples: list[CmdletExample] = []

        # Find examples section
        examples_match = re.search(
            r"## EXAMPLES\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        if not examples_match:
            return examples

        examples_content = examples_match.group(1)

        # Find each example
        example_pattern = r"### EXAMPLE (\d+)\s*\n\n```powershell\s*\n(.*?)\n```\s*\n\n(.*?)(?=\n### EXAMPLE|\n## |\Z)"

        for match in re.finditer(example_pattern, examples_content, re.DOTALL):
            example_num = match.group(1)
            code = match.group(2).strip()
            description = match.group(3).strip()

            example = CmdletExample(
                title=f"Example {example_num}", code=code, description=description
            )
            examples.append(example)

        return examples

    def _extract_notes(self, content: str) -> str:
        """Extract notes section"""
        match = re.search(r"## NOTES\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_inputs(self, content: str) -> str:
        """Extract inputs section"""
        match = re.search(r"## INPUTS\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_outputs(self, content: str) -> str:
        """Extract outputs section"""
        match = re.search(r"## OUTPUTS\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _extract_related_links(self, content: str) -> List[str]:
        """Extract related links section"""
        links = []

        match = re.search(
            r"## RELATED LINKS\s*\n(.*?)(?=\n## |\n---|\Z)", content, re.DOTALL
        )
        if match:
            links_content = match.group(1)
            # Find all URLs
            url_pattern = r"https?://[^\s\])]+"
            links = re.findall(url_pattern, links_content)

        return links

    def get_cmdlet_names(self) -> List[str]:
        """Get list of all parsed cmdlet names"""
        return list(self.cmdlets.keys())

    def get_cmdlet(self, name: str) -> Optional[CmdletDefinition]:
        """Get cmdlet definition by name"""
        return self.cmdlets.get(name)

    def export_to_json(self, output_file: str) -> None:
        """Export parsed cmdlets to JSON file"""
        import json
        from dataclasses import asdict

        def serialize_enum(obj: object) -> str | list[object]:
            if isinstance(obj, ParameterType):
                return obj.value
            elif isinstance(obj, set):
                return list(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        cmdlets_data = {}
        for name, cmdlet in self.cmdlets.items():
            cmdlets_data[name] = asdict(cmdlet)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(
                cmdlets_data, f, indent=2, default=serialize_enum, ensure_ascii=False
            )

        logger.info(f"Exported {len(self.cmdlets)} cmdlets to {output_file}")

    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of parsed cmdlets for validation"""
        total_cmdlets = len(self.cmdlets)
        total_parameters = sum(len(c.parameters) for c in self.cmdlets.values())
        cmdlets_with_examples = sum(1 for c in self.cmdlets.values() if c.examples)
        cmdlets_with_param_sets = sum(
            1 for c in self.cmdlets.values() if c.parameter_sets
        )

        return {
            "total_cmdlets": total_cmdlets,
            "total_parameters": total_parameters,
            "cmdlets_with_examples": cmdlets_with_examples,
            "cmdlets_with_parameter_sets": cmdlets_with_param_sets,
            "coverage_percentage": round(
                (cmdlets_with_examples / total_cmdlets * 100)
                if total_cmdlets > 0
                else 0,
                2,
            ),
        }
