from typing import List

"""Metadata extractor for MSI and EXE files using cross-platform tools."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from installer files using cross-platform tools."""

    def extract_executable_names(self, file_path: str) -> List[str]:
        """
        Extracts executable names from an MSI's Icon and Shortcut tables.
        """
        if not file_path.lower().endswith(".msi"):
            return []

        if not self._is_msitools_available():
            logger.warning("msitools not available, cannot extract executable names.")
            return []

        executables = set()

        for table in ["Icon", "Shortcut"]:
            try:
                cmd = ["msiinfo", "export", file_path, table]
                result = subprocess.run(
                    cmd, capture_output=True, text=True, check=False, timeout=30
                )
                if result.returncode == 0:
                    content = result.stdout
                    import re

                    found = re.findall(r"(\w+\.exe)", content, re.IGNORECASE)
                    for exe in found:
                        executables.add(exe.lower())
                else:
                    logger.warning(
                        f"msiinfo failed for table {table} with exit code {result.returncode}: {result.stderr}"
                    )

            except Exception as e:
                logger.warning(
                    f"Could not extract executables from MSI table '{table}': {e}"
                )

        return sorted(list(executables))

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from an installer file.

        Args:
            file_path: Path to the installer file

        Returns:
            Dictionary containing extracted metadata
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Determine file type by extension
        extension = file_path_obj.suffix.lower()

        if extension == ".msi":
            return self._extract_msi_metadata(file_path)
        elif extension == ".exe":
            return self._extract_exe_metadata(file_path)
        else:
            logger.warning(f"Unsupported file type: {extension}")
            return self._extract_basic_metadata(file_path)

    def _extract_basic_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract basic file metadata.

        Args:
            file_path: Path to the file

        Returns:
            Basic metadata dictionary
        """
        file_path_obj = Path(file_path)
        stat = file_path_obj.stat()

        return {
            "filename": file_path_obj.name,
            "file_size": stat.st_size,
            "file_extension": file_path_obj.suffix.lower(),
            "product_name": None,
            "version": None,
            "publisher": None,
            "install_date": None,
            "uninstall_string": None,
            "estimated_size": stat.st_size,
            "product_code": None,
            "upgrade_code": None,
            "language": None,
            "architecture": None,
        }

    def _extract_msi_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from MSI file using msitools.

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        logger.info(f"Extracting MSI metadata from: {file_path}")

        # Start with basic metadata
        metadata = self._extract_basic_metadata(file_path)

        try:
            # Try msitools first (preferred method)
            if self._is_msitools_available():
                metadata.update(self._extract_with_msitools(file_path))
            else:
                logger.info("msitools not available, trying alternative methods")
                # Fallback to other methods
                metadata.update(self._extract_msi_alternative(file_path))

        except Exception as e:
            logger.warning(f"Failed to extract MSI metadata: {e}")
            # Return basic metadata if extraction fails

        return metadata

    def _is_msitools_available(self) -> bool:
        """Check if msitools (msiinfo) is available.

        Returns:
            True if msitools is available, False otherwise
        """
        try:
            result = subprocess.run(
                ["msiinfo", "--help"], capture_output=True, check=False, timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _extract_with_msitools(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using msitools (recommended approach).

        This implements the approach recommended in the PDF:
        1. Use 'msiinfo suminfo' to get summary information
        2. Use 'msiinfo export Property' to get exact property values
        3. Parse Template field for architecture information

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # Step 1: Get summary information
            summary_info = self._get_msi_summary_info(file_path)
            metadata.update(summary_info)

            # Step 2: Get property table for exact values
            property_info = self._get_msi_property_table(file_path)
            metadata.update(property_info)

            # Step 3: Parse architecture from Template field
            if "template" in metadata:
                arch_info = self._parse_template_architecture(metadata["template"])
                metadata.update(arch_info)

        except Exception as e:
            logger.warning(f"msitools extraction failed: {e}")

        return metadata

    def _get_msi_summary_info(self, file_path: str) -> Dict[str, Any]:
        """Get MSI summary information using 'msiinfo suminfo'.

        Args:
            file_path: Path to the MSI file

        Returns:
            Dictionary with summary information
        """
        metadata: Dict[str, Any] = {}

        try:
            cmd = ["msiinfo", "suminfo", file_path]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )

            # Parse the summary info output
            for line in result.stdout.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip().lower()
                    value = value.strip()

                    # Map summary fields to our metadata
                    if key == "title":
                        metadata["summary_title"] = value
                    elif key == "subject":
                        metadata["summary_subject"] = value
                    elif key == "author":
                        metadata["summary_author"] = value
                    elif key == "template":
                        metadata["template"] = value
                    elif key == "comments":
                        metadata["summary_comments"] = value

            logger.debug(f"MSI summary info extracted: {metadata}")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to get MSI summary info: {e}")
        except subprocess.TimeoutExpired:
            logger.warning("MSI summary info extraction timed out")

        return metadata

    def _get_msi_property_table(self, file_path: str) -> Dict[str, Any]:
        """Get MSI property table using 'msiinfo export Property'.

        Args:
            file_path: Path to the MSI file

        Returns:
            Dictionary with property table values
        """
        metadata: Dict[str, Any] = {}

        try:
            cmd = ["msiinfo", "export", file_path, "Property"]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=False, timeout=30
            )
            if result.returncode == 0:
                content = result.stdout
            else:
                logger.warning(
                    f"msiinfo failed for Property table with exit code {result.returncode}: {result.stderr}"
                )
                content = ""

            # Parse property table format (tab-separated values)
            properties = self._parse_property_table(content)

            # Map MSI properties to our metadata fields
            metadata.update(
                {
                    "product_name": properties.get("ProductName"),
                    "version": properties.get("ProductVersion"),
                    "publisher": properties.get("Manufacturer"),
                    "product_code": properties.get("ProductCode"),
                    "upgrade_code": properties.get("UpgradeCode"),
                    "language": properties.get("ProductLanguage"),
                }
            )

            logger.debug(f"MSI properties extracted: {len(properties)} properties")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to export MSI property table: {e}")
        except subprocess.TimeoutExpired:
            logger.warning("MSI property table export timed out")
        except Exception as e:
            logger.warning(f"Error processing MSI property table: {e}")

        return metadata

    def _parse_property_table(self, content: str) -> Dict[str, str]:
        """Parse MSI property table content.

        Args:
            content: Raw property table content

        Returns:
            Dictionary of property name -> value
        """
        properties = {}

        lines = content.strip().split("\n")
        for line in lines:
            # Skip header lines and empty lines
            if not line.strip() or line.startswith("Property") or line.startswith("s"):
                continue

            # Parse tab-separated values
            parts = line.split("\t")
            if len(parts) >= 2:
                prop_name = parts[0].strip()
                prop_value = parts[1].strip()
                if prop_name and prop_value:
                    properties[prop_name] = prop_value

        return properties

    def _parse_template_architecture(self, template: str) -> Dict[str, Any]:
        """Parse architecture information from MSI Template field.

        According to the PDF, Template format is: platform;language_ids
        - Empty or "Intel" = x86 (32-bit)
        - "x64" or "Intel64" = x64 (64-bit)
        - "Arm64" = ARM 64-bit

        Args:
            template: Template string from MSI summary

        Returns:
            Dictionary with architecture and language info
        """
        metadata: Dict[str, Any] = {}

        if not template:
            return metadata

        try:
            # Split on semicolon: platform;language_ids
            parts = template.split(";")
            platform = parts[0].strip() if parts else ""

            # Determine architecture
            if not platform or platform.lower() == "intel":
                metadata["architecture"] = "x86"
            elif platform.lower() in ["x64", "intel64"]:
                metadata["architecture"] = "x64"
            elif platform.lower() in ["x64", "intel64"]:
                metadata["architecture"] = "x64"
            elif platform.lower() == "arm64":
                metadata["architecture"] = "arm64"
            else:
                metadata["architecture"] = platform  # Keep original if unknown

            # Parse language codes if present
            if len(parts) > 1:
                lang_codes = parts[1].strip()
                if lang_codes:
                    # Map common language codes
                    lang_map = {
                        "1033": "en-US",
                        "1031": "de-DE",
                        "1036": "fr-FR",
                        "1040": "it-IT",
                        "1034": "es-ES",
                    }
                    metadata["language_code"] = lang_codes
                    metadata["language"] = lang_map.get(lang_codes, lang_codes)

        except Exception as e:
            logger.warning(f"Failed to parse template '{template}': {e}")

        return metadata

    def _extract_msi_alternative(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using alternative methods when msitools is not available.

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # Try lessmsi if available (fallback option)
            if self._is_lessmsi_available():
                metadata.update(self._extract_with_lessmsi(file_path))
            else:
                logger.info("No alternative MSI extraction tools available")
                # Could add more fallback methods here (Wine, etc.)

        except Exception as e:
            logger.warning(f"Alternative MSI extraction failed: {e}")

        return metadata

    def _is_lessmsi_available(self) -> bool:
        """Check if lessmsi is available.

        Returns:
            True if lessmsi is available, False otherwise
        """
        try:
            subprocess.run(["lessmsi"], capture_output=True, check=False, timeout=5)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _extract_with_lessmsi(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using lessmsi (fallback method).

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # Use lessmsi to list MSI information
            cmd = ["lessmsi", "l", file_path]
            result = subprocess.run(
                cmd, capture_output=True, text=True, check=True, timeout=30
            )

            # Parse lessmsi output (this is a simplified parser)
            lines = result.stdout.split("\n")
            for line in lines:
                if "ProductName" in line and ":" in line:
                    metadata["product_name"] = line.split(":", 1)[1].strip()
                elif "ProductVersion" in line and ":" in line:
                    metadata["version"] = line.split(":", 1)[1].strip()
                elif "Manufacturer" in line and ":" in line:
                    metadata["publisher"] = line.split(":", 1)[1].strip()

        except subprocess.CalledProcessError as e:
            logger.warning(f"LessMSI extraction failed: {e}")
        except subprocess.TimeoutExpired:
            logger.warning("LessMSI extraction timed out")

        return metadata

    def _extract_exe_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from EXE file using PE header analysis.

        Args:
            file_path: Path to the EXE file

        Returns:
            EXE metadata dictionary
        """
        logger.info(f"Extracting EXE metadata from: {file_path}")

        # Start with basic metadata
        metadata = self._extract_basic_metadata(file_path)

        try:
            # Extract PE header information
            metadata.update(self._extract_pe_metadata(file_path))

        except Exception as e:
            logger.warning(f"Failed to extract PE metadata: {e}")

        return metadata

    def _extract_pe_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract metadata from PE header.

        Args:
            file_path: Path to the EXE file

        Returns:
            PE metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            with open(file_path, "rb") as f:
                # Read DOS header
                dos_header = f.read(64)
                if len(dos_header) < 64 or dos_header[:2] != b"MZ":
                    raise ValueError("Invalid PE file - missing DOS header")

                # Get PE header offset
                pe_offset = int.from_bytes(dos_header[60:64], "little")

                # Read PE header
                f.seek(pe_offset)
                pe_signature = f.read(4)
                if pe_signature != b"PE\x00\x00":
                    raise ValueError("Invalid PE file - missing PE signature")

                # Read COFF header
                coff_header = f.read(20)
                if len(coff_header) < 20:
                    raise ValueError("Invalid PE file - incomplete COFF header")

                # Extract machine type (architecture)
                machine = int.from_bytes(coff_header[0:2], "little")
                if machine == 0x014C:
                    metadata["architecture"] = "x86"
                elif machine == 0x8664:
                    metadata["architecture"] = "x64"
                elif machine == 0x01C4:
                    metadata["architecture"] = "ARM"
                else:
                    metadata["architecture"] = f"Unknown (0x{machine:04x})"

                # Try to extract version information from resources
                metadata.update(self._extract_version_info(file_path))

        except Exception as e:
            logger.warning(f"PE header extraction failed: {e}")

        return metadata

    def _extract_version_info(self, file_path: str) -> Dict[str, Any]:
        """Extract version information from PE resources.

        Args:
            file_path: Path to the EXE file

        Returns:
            Version information dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # On Windows, we could use win32api to extract version info
            # For cross-platform compatibility, we'll use a basic approach
            if os.name == "nt":
                metadata.update(self._extract_version_info_windows(file_path))
            else:
                # For non-Windows systems, we could use tools like 'file' command
                # or implement a basic PE resource parser
                logger.debug("Version info extraction not implemented for non-Windows")

        except Exception as e:
            logger.debug(f"Version info extraction failed: {e}")

        return metadata

    def _extract_version_info_windows(self, file_path: str) -> Dict[str, Any]:
        """Extract version info on Windows using win32api.

        Args:
            file_path: Path to the EXE file

        Returns:
            Version information dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # This would require pywin32 package
            # import win32api
            # import win32file

            # For now, we'll simulate the extraction
            logger.debug(f"Would extract Windows version info from: {file_path}")

            # In a real implementation, you would:
            # 1. Use GetFileVersionInfo to get version info
            # 2. Parse the version info structure
            # 3. Extract ProductName, ProductVersion, CompanyName, etc.

        except Exception as e:
            logger.debug(f"Windows version info extraction failed: {e}")

        return metadata

    def get_psadt_variables(self, metadata: Dict[str, Any]) -> Dict[str, str]:
        """Extract PSADT-specific variables from metadata.

        Maps extracted metadata to PSADT template variables:
        - appName: Product name from MSI/EXE
        - appVersion: Product version
        - appVendor: Publisher/Manufacturer
        - productCode: MSI Product Code (GUID)

        Uses fallback logic to get values from summary info if property table is not available.

        Args:
            metadata: Dictionary containing extracted metadata

        Returns:
            Dictionary containing PSADT variables
        """
        # Primary sources (from Property table)
        app_name = metadata.get("product_name")
        app_version = metadata.get("version")
        app_vendor = metadata.get("publisher")
        product_code = metadata.get("product_code")

        # Fallback to summary information if property table values are not available
        if not app_name:
            # Try summary_subject first, then summary_title
            app_name = metadata.get("summary_subject") or metadata.get("summary_title")
            # Clean up common installer database titles
            if app_name and app_name.lower() in [
                "installation database",
                "installer database",
            ]:
                app_name = None

        if not app_vendor:
            # Use summary_author as vendor fallback
            app_vendor = metadata.get("summary_author")

        # Try to extract version from summary_comments if not available from property table
        if not app_version:
            comments = metadata.get("summary_comments", "")
            if comments:
                # Try to extract version from comments like "136.0.7103.114 Copyright 2025 Google LLC"
                import re

                # Look for version patterns like X.Y.Z.W or X.Y.Z
                version_match = re.search(r"(\d+\.\d+\.\d+(?:\.\d+)?)", comments)
                if version_match:
                    app_version = version_match.group(1)

        psadt_vars = {
            "appName": app_name or "",
            "appVersion": app_version or "",
            "appVendor": app_vendor or "",
            "productCode": product_code or "",
        }

        return psadt_vars


def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """Convenience function to extract metadata from a file.

    Args:
        file_path: Path to the installer file

    Returns:
        Dictionary containing extracted metadata
    """
    extractor = MetadataExtractor()
    return extractor.extract_metadata(file_path)

</file_content>

Now that you have the latest state of the file, try the operation again with fewer, more precise SEARCH blocks. For large files especially, it may be prudent to try to limit yourself to <5 SEARCH/REPLACE blocks at a time, then wait for the user to respond with the result of the operation before following up with another replace_in_file call to make additional edits.
(If you run into this error 3 times in a row, you may use the write_to_file tool as a fallback.)
</error><environment_details>
# VSCode Visible Files
../../../../../src/app/routes.py
../../../../../src/app/routes.py
src/app/metadata_extractor.py

# VSCode Open Tabs
.clinerules
src/app/database.py
src/aipackager/workflow.py
src/app/services/advisor_service.py
src/app/services/instruction_processor.py
src/app/prompts/instruction_processing.j2
instance/logs/894f360c-7cd4-4a13-a0c1-55786b697f5d.log
src/app/services/cmdlet_discovery.py
src/app/prompts/script_generation.j2
additional-tasks.md
src/app/models.py
src/app/script_renderer.py
src/app/templates/psadt/Invoke-AppDeployToolkit.ps1.j2
closeapps-problem.md
src/app/services/script_generator.py
src/app/routes.py
src/app/metadata_extractor.py

# Current Time
28.6.2025, 4:17:36 PM (Europe/Berlin, UTC+2:00)

# Context Window Usage
109.517 / 1.048,576K tokens used (10%)

# Current Mode
ACT MODE
</environment_details>
