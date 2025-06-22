"""Metadata extractor for MSI and EXE files."""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract metadata from installer files."""

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
        """Extract metadata from MSI file.

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        logger.info(f"Extracting MSI metadata from: {file_path}")

        # Start with basic metadata
        metadata = self._extract_basic_metadata(file_path)

        try:
            # Try to use msiexec to query MSI properties (Windows only)
            if os.name == "nt":
                metadata.update(self._extract_msi_with_msiexec(file_path))
            else:
                # On non-Windows systems, try alternative methods
                metadata.update(self._extract_msi_alternative(file_path))

        except Exception as e:
            logger.warning(f"Failed to extract MSI metadata: {e}")
            # Return basic metadata if extraction fails

        return metadata

    def _extract_msi_with_msiexec(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using msiexec (Windows only).

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        # Properties to extract from MSI
        msi_properties = {
            "ProductName": "product_name",
            "ProductVersion": "version",
            "Manufacturer": "publisher",
            "ProductCode": "product_code",
            "UpgradeCode": "upgrade_code",
            "ProductLanguage": "language",
        }

        for msi_prop, metadata_key in msi_properties.items():
            try:
                # This is a simplified approach - in practice, you'd need
                # more sophisticated MSI property extraction
                logger.debug(f"Would extract MSI property: {msi_prop}")

            except Exception as e:
                logger.debug(f"Failed to extract {msi_prop}: {e}")

        return metadata

    def _extract_msi_alternative(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using alternative methods (cross-platform).

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # Try to use lessmsi if available (cross-platform MSI extractor)
            if self._is_lessmsi_available():
                metadata.update(self._extract_with_lessmsi(file_path))
            else:
                logger.info("LessMSI not available, using basic extraction")
                # Could implement other extraction methods here

        except Exception as e:
            logger.warning(f"Alternative MSI extraction failed: {e}")

        return metadata

    def _is_lessmsi_available(self) -> bool:
        """Check if lessmsi is available.

        Returns:
            True if lessmsi is available, False otherwise
        """
        try:
            subprocess.run(["lessmsi"], capture_output=True, check=False)
            return True
        except FileNotFoundError:
            return False

    def _extract_with_lessmsi(self, file_path: str) -> Dict[str, Any]:
        """Extract MSI metadata using lessmsi.

        Args:
            file_path: Path to the MSI file

        Returns:
            MSI metadata dictionary
        """
        metadata: Dict[str, Any] = {}

        try:
            # Use lessmsi to extract MSI information
            cmd = ["lessmsi", "l", file_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Parse lessmsi output to extract metadata
            # This is a simplified parser - real implementation would be more robust
            lines = result.stdout.split("\n")
            for line in lines:
                if "ProductName" in line:
                    metadata["product_name"] = line.split(":", 1)[1].strip()
                elif "ProductVersion" in line:
                    metadata["version"] = line.split(":", 1)[1].strip()
                elif "Manufacturer" in line:
                    metadata["publisher"] = line.split(":", 1)[1].strip()

        except subprocess.CalledProcessError as e:
            logger.warning(f"LessMSI extraction failed: {e}")

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
                # This is a simplified implementation
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


def extract_file_metadata(file_path: str) -> Dict[str, Any]:
    """Convenience function to extract metadata from a file.

    Args:
        file_path: Path to the installer file

    Returns:
        Dictionary containing extracted metadata
    """
    extractor = MetadataExtractor()
    return extractor.extract_metadata(file_path)
