"""Tests for metadata extractor functionality."""

import tempfile
from pathlib import Path
import pytest

from src.app.metadata_extractor import MetadataExtractor, extract_file_metadata


class TestMetadataExtractor:
    """Test metadata extraction functionality."""

    def test_extract_basic_metadata(self):
        """Test basic metadata extraction."""
        extractor = MetadataExtractor()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_basic_metadata(temp_path)

            assert metadata["filename"] == Path(temp_path).name
            assert metadata["file_size"] > 0
            assert metadata["file_extension"] == ".txt"
            assert metadata["product_name"] is None
            assert metadata["version"] is None
            assert metadata["publisher"] is None
            assert metadata["estimated_size"] == metadata["file_size"]

        finally:
            Path(temp_path).unlink()

    def test_extract_metadata_file_not_found(self):
        """Test metadata extraction with non-existent file."""
        extractor = MetadataExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.extract_metadata("/nonexistent/file.msi")

    def test_extract_metadata_unsupported_file_type(self):
        """Test metadata extraction with unsupported file type."""
        extractor = MetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extractor.extract_metadata(temp_path)

            # Should return basic metadata for unsupported types
            assert metadata["filename"] == Path(temp_path).name
            assert metadata["file_extension"] == ".txt"

        finally:
            Path(temp_path).unlink()

    def test_extract_msi_metadata_basic(self):
        """Test MSI metadata extraction (basic functionality)."""
        extractor = MetadataExtractor()

        # Create a fake MSI file (just for testing the flow)
        with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as temp_file:
            temp_file.write(b"Fake MSI content")
            temp_path = temp_file.name

        try:
            metadata = extractor.extract_metadata(temp_path)

            # Should contain basic metadata
            assert metadata["filename"] == Path(temp_path).name
            assert metadata["file_extension"] == ".msi"
            assert metadata["file_size"] > 0

        finally:
            Path(temp_path).unlink()

    def test_extract_exe_metadata_basic(self):
        """Test EXE metadata extraction (basic functionality)."""
        extractor = MetadataExtractor()

        # Create a fake EXE file (just for testing the flow)
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Fake EXE content")
            temp_path = temp_file.name

        try:
            metadata = extractor.extract_metadata(temp_path)

            # Should contain basic metadata
            assert metadata["filename"] == Path(temp_path).name
            assert metadata["file_extension"] == ".exe"
            assert metadata["file_size"] > 0

        finally:
            Path(temp_path).unlink()

    def test_extract_pe_metadata_invalid_file(self):
        """Test PE metadata extraction with invalid PE file."""
        extractor = MetadataExtractor()

        # Create a file that's not a valid PE file
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Not a PE file")
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_pe_metadata(temp_path)

            # Should return empty metadata for invalid PE file
            assert isinstance(metadata, dict)

        finally:
            Path(temp_path).unlink()

    def test_extract_pe_metadata_valid_dos_header(self):
        """Test PE metadata extraction with valid DOS header."""
        extractor = MetadataExtractor()

        # Create a file with valid DOS header but invalid PE
        dos_header = b"MZ" + b"\x00" * 58 + b"\x80\x00\x00\x00"  # PE offset at 0x80
        coff_header = (
            b"\x4c\x01" + b"\x00" * 18
        )  # x86 machine type + rest of COFF header

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(
                dos_header
                + b"\x00" * (0x80 - len(dos_header))
                + b"PE\x00\x00"
                + coff_header
            )
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_pe_metadata(temp_path)

            # Should extract architecture from COFF header
            assert metadata.get("architecture") == "x86"

        finally:
            Path(temp_path).unlink()

    def test_extract_pe_metadata_x64_architecture(self):
        """Test PE metadata extraction with x64 architecture."""
        extractor = MetadataExtractor()

        # Create a file with x64 machine type
        dos_header = b"MZ" + b"\x00" * 58 + b"\x80\x00\x00\x00"
        coff_header = b"\x64\x86" + b"\x00" * 18  # x64 machine type

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(
                dos_header
                + b"\x00" * (0x80 - len(dos_header))
                + b"PE\x00\x00"
                + coff_header
            )
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_pe_metadata(temp_path)

            assert metadata.get("architecture") == "x64"

        finally:
            Path(temp_path).unlink()

    def test_is_lessmsi_available(self):
        """Test lessmsi availability check."""
        extractor = MetadataExtractor()

        # This will likely return False unless lessmsi is installed
        result = extractor._is_lessmsi_available()
        assert isinstance(result, bool)

    def test_extract_with_lessmsi_not_available(self):
        """Test lessmsi extraction when not available."""
        extractor = MetadataExtractor()

        # Create a fake MSI file
        with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as temp_file:
            temp_file.write(b"Fake MSI content")
            temp_path = temp_file.name

        try:
            # Skip test if lessmsi is not available (which is expected)
            if extractor._is_lessmsi_available():
                # If lessmsi is available, test that it returns metadata
                metadata = extractor._extract_with_lessmsi(temp_path)
                assert isinstance(metadata, dict)
            else:
                # Just verify that the function exists and can be called safely
                # We don't actually call it since lessmsi is not available
                assert hasattr(extractor, "_extract_with_lessmsi")

        finally:
            Path(temp_path).unlink()

    def test_convenience_function(self):
        """Test the convenience function."""
        with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extract_file_metadata(temp_path)

            assert metadata["filename"] == Path(temp_path).name
            assert metadata["file_extension"] == ".msi"

        finally:
            Path(temp_path).unlink()

    def test_extract_msi_metadata_with_pymsi(self):
        """Test MSI metadata extraction with real MSI file."""
        # This test uses a real MSI file to verify the extraction flow
        msi_path = "googlechromestandaloneenterprise_136.0.0_64bit.msi"
        metadata = extract_file_metadata(msi_path)

        # Verify basic file metadata is extracted
        assert (
            metadata["filename"] == "googlechromestandaloneenterprise_136.0.0_64bit.msi"
        )
        assert metadata["file_extension"] == ".msi"
        assert metadata["file_size"] > 0

        # Verify all expected metadata fields are present (even if None)
        assert "product_name" in metadata
        assert "version" in metadata
        assert "publisher" in metadata
        assert "product_code" in metadata

    def test_extract_psadt_variables(self):
        """Test extraction of PSADT-specific variables from MSI metadata."""
        extractor = MetadataExtractor()

        # Test with the real Chrome MSI file
        msi_path = "googlechromestandaloneenterprise_136.0.0_64bit.msi"
        metadata = extractor.extract_metadata(msi_path)

        # Test that PSADT variables can be derived from metadata
        psadt_vars = extractor.get_psadt_variables(metadata)

        # Verify PSADT variables are present and correctly mapped
        assert "appName" in psadt_vars
        assert "appVersion" in psadt_vars
        assert "appVendor" in psadt_vars
        assert "productCode" in psadt_vars

        # With the improved implementation using msitools, we can now extract real data
        # from the Chrome MSI file using summary information as fallback
        assert (
            psadt_vars["appName"] == "Google Chrome Installer"
        )  # From summary_subject
        assert psadt_vars["appVersion"] == ""  # Version not available in summary
        assert psadt_vars["appVendor"] == "Google LLC"  # From summary_author
        assert psadt_vars["productCode"] == ""  # Product code not available in summary

    def test_get_psadt_variables_with_basic_metadata(self):
        """Test PSADT variables extraction with basic metadata."""
        extractor = MetadataExtractor()

        # Create test metadata
        test_metadata = {
            "product_name": "Test Application",
            "version": "1.0.0",
            "publisher": "Test Publisher",
            "product_code": "{12345678-1234-1234-1234-123456789012}",
            "architecture": "x64",
        }

        psadt_vars = extractor.get_psadt_variables(test_metadata)

        assert psadt_vars["appName"] == "Test Application"
        assert psadt_vars["appVersion"] == "1.0.0"
        assert psadt_vars["appVendor"] == "Test Publisher"
        assert psadt_vars["productCode"] == "{12345678-1234-1234-1234-123456789012}"

    def test_get_psadt_variables_with_missing_fields(self):
        """Test PSADT variables extraction with missing metadata fields."""
        extractor = MetadataExtractor()

        # Create metadata with missing fields
        test_metadata = {
            "product_name": "Test App",
            "version": None,
            "publisher": None,
            "product_code": None,
        }

        psadt_vars = extractor.get_psadt_variables(test_metadata)

        assert psadt_vars["appName"] == "Test App"
        assert psadt_vars["appVersion"] == ""  # Should default to empty string
        assert psadt_vars["appVendor"] == ""  # Should default to empty string
        assert psadt_vars["productCode"] == ""  # Should default to empty string

    def test_metadata_structure_completeness(self):
        """Test that metadata contains all expected fields."""
        extractor = MetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extractor.extract_metadata(temp_path)

            # Check that all expected fields are present
            expected_fields = [
                "filename",
                "file_size",
                "file_extension",
                "product_name",
                "version",
                "publisher",
                "install_date",
                "uninstall_string",
                "estimated_size",
                "product_code",
                "upgrade_code",
                "language",
                "architecture",
            ]

            for field in expected_fields:
                assert field in metadata

        finally:
            Path(temp_path).unlink()

    def test_extract_msi_alternative_methods(self):
        """Test MSI alternative extraction methods."""
        extractor = MetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".msi", delete=False) as temp_file:
            temp_file.write(b"Fake MSI content")
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_msi_alternative(temp_path)
            assert isinstance(metadata, dict)

        finally:
            Path(temp_path).unlink()

    def test_extract_version_info(self):
        """Test version info extraction."""
        extractor = MetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_version_info(temp_path)
            assert isinstance(metadata, dict)

        finally:
            Path(temp_path).unlink()

    def test_extract_version_info_windows(self):
        """Test Windows-specific version info extraction."""
        extractor = MetadataExtractor()

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Test content")
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_version_info_windows(temp_path)
            assert isinstance(metadata, dict)

        finally:
            Path(temp_path).unlink()

    def test_is_msitools_available(self):
        """Test msitools availability check."""
        extractor = MetadataExtractor()

        # This will return True if msitools is installed, False otherwise
        result = extractor._is_msitools_available()
        assert isinstance(result, bool)

    def test_file_size_calculation(self):
        """Test that file size is calculated correctly."""
        extractor = MetadataExtractor()

        test_content = b"A" * 1024  # 1KB of data
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(test_content)
            temp_path = temp_file.name

        try:
            metadata = extractor.extract_metadata(temp_path)

            assert metadata["file_size"] == 1024
            assert metadata["estimated_size"] == 1024

        finally:
            Path(temp_path).unlink()

    def test_case_insensitive_extension_handling(self):
        """Test that file extensions are handled case-insensitively."""
        extractor = MetadataExtractor()

        # Test with uppercase extensions
        test_cases = [".MSI", ".EXE", ".Msi", ".Exe"]

        for extension in test_cases:
            with tempfile.NamedTemporaryFile(
                suffix=extension, delete=False
            ) as temp_file:
                temp_file.write(b"Test content")
                temp_path = temp_file.name

            try:
                metadata = extractor.extract_metadata(temp_path)

                # Extension should be normalized to lowercase
                assert metadata["file_extension"] == extension.lower()

            finally:
                Path(temp_path).unlink()

    def test_error_handling_in_pe_extraction(self):
        """Test error handling in PE extraction."""
        extractor = MetadataExtractor()

        # Test with file that's too small
        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(b"Small")  # Too small to be a valid PE file
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_pe_metadata(temp_path)
            # Should return empty dict on error
            assert isinstance(metadata, dict)

        finally:
            Path(temp_path).unlink()

    def test_unknown_architecture_handling(self):
        """Test handling of unknown architecture types."""
        extractor = MetadataExtractor()

        # Create a file with unknown machine type
        dos_header = b"MZ" + b"\x00" * 58 + b"\x80\x00\x00\x00"
        coff_header = b"\xff\xff" + b"\x00" * 18  # Unknown machine type

        with tempfile.NamedTemporaryFile(suffix=".exe", delete=False) as temp_file:
            temp_file.write(
                dos_header
                + b"\x00" * (0x80 - len(dos_header))
                + b"PE\x00\x00"
                + coff_header
            )
            temp_path = temp_file.name

        try:
            metadata = extractor._extract_pe_metadata(temp_path)

            # Should handle unknown architecture gracefully
            assert "architecture" in metadata
            assert "Unknown" in metadata["architecture"]

        finally:
            Path(temp_path).unlink()
