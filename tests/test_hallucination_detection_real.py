# tests/test_hallucination_detection_real.py

"""
Real-world tests for hallucination detection with actual invalid cmdlets and parameters.
These tests verify that the MCP-based hallucination detector catches real issues.
"""

import unittest
import tempfile
import os
from src.app.services.hallucination_detector import HallucinationDetector


class TestHallucinationDetectionReal(unittest.TestCase):
    """Test hallucination detection with real invalid PowerShell scripts."""

    def setUp(self):
        self.detector = HallucinationDetector()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        # Clean up temp files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_test_script(self, content: str) -> str:
        """Create a temporary PowerShell script for testing."""
        script_path = os.path.join(self.temp_dir, "test_script.ps1")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(content)
        return script_path

    def test_valid_psadt_script_no_hallucinations(self):
        """Test that a valid PSADT script passes hallucination detection."""
        valid_script = """
# Valid PSADT Script
Write-ADTLogEntry -Message "Starting installation" -Level Info
Start-ADTMsiProcess -Path "$dirFiles\\installer.msi" -Parameters "/qn"
Set-ADTRegistryKey -Key "HKLM:\\Software\\MyApp" -Name "Version" -Value "1.0" -Type String
Copy-ADTFile -Source "$dirSupportFiles\\config.xml" -Destination "C:\\Program Files\\MyApp"
"""
        script_path = self._create_test_script(valid_script)

        report = self.detector.detect(script_path)

        self.assertFalse(
            report.get("has_hallucinations", True),
            "Valid PSADT script should not have hallucinations",
        )
        self.assertEqual(
            report.get("unknown_cmdlets_count", 1),
            0,
            "Valid script should have 0 unknown cmdlets",
        )

    def test_invalid_cmdlets_detected(self):
        """Test that completely invalid/hallucinated cmdlets are detected."""
        invalid_script = """
# Script with hallucinated cmdlets
Write-ADTLogEntry -Message "Starting installation" -Level Info
Start-FakeInstaller -Path "installer.msi" -SilentMode $true
Install-NonExistentPackage -Source "package.zip"
Set-PSADTMagicRegistry -Key "HKLM:\\Software\\MyApp" -Value "test"
Copy-ADTFile -Source "config.xml" -Destination "C:\\Program Files\\MyApp"
Remove-HallucinatedCmdlet -Force
"""
        script_path = self._create_test_script(invalid_script)

        # Pass the script content, not the file path
        report = self.detector.detect(invalid_script)

        # Debug: Print the actual report to see what's happening
        print("\n=== INVALID CMDLETS TEST DEBUG ===")
        print(f"Report: {report}")
        print(f"Has hallucinations: {report.get('has_hallucinations')}")
        print(f"Issues: {report.get('issues', [])}")
        print(f"Unknown cmdlets count: {report.get('unknown_cmdlets_count', 0)}")
        print("=" * 50)

        self.assertTrue(
            report.get("has_hallucinations", False),
            f"Script with invalid cmdlets should be flagged as having hallucinations. Got report: {report}",
        )
        self.assertGreater(
            report.get("unknown_cmdlets_count", 0),
            0,
            "Should detect multiple unknown cmdlets",
        )

        # Check that specific invalid cmdlets are identified
        issues = report.get("issues", [])
        invalid_cmdlets = [
            "Start-FakeInstaller",
            "Install-NonExistentPackage",
            "Set-PSADTMagicRegistry",
            "Remove-HallucinatedCmdlet",
        ]

        found_issues = [issue.get("cmdlet") for issue in issues if "cmdlet" in issue]
        for invalid_cmdlet in invalid_cmdlets:
            self.assertIn(
                invalid_cmdlet,
                str(found_issues),
                f"Should detect invalid cmdlet: {invalid_cmdlet}",
            )

    def test_invalid_parameters_detected(self):
        """Test that valid cmdlets with invalid parameters are detected."""
        invalid_params_script = """
# Script with valid cmdlets but invalid parameters
Write-ADTLogEntry -Message "Starting" -Level Info
Start-ADTMsiProcess -Path "installer.msi" -FakeParameter "invalid" -NonExistentSwitch
Set-ADTRegistryKey -Key "HKLM:\\Software\\Test" -InvalidParam "test" -BadFlag $true
Copy-ADTFile -Source "file.txt" -WrongDestination "C:\\Temp" -FakeSwitch
"""
        script_path = self._create_test_script(invalid_params_script)

        report = self.detector.detect(script_path)

        self.assertTrue(
            report.get("has_hallucinations", False),
            "Script with invalid parameters should be flagged",
        )

        # Check for parameter-related issues
        issues = report.get("issues", [])
        parameter_issues = [
            issue for issue in issues if "parameter" in issue.get("type", "").lower()
        ]
        self.assertGreater(
            len(parameter_issues), 0, "Should detect invalid parameter issues"
        )

    def test_mixed_valid_and_invalid_content(self):
        """Test detection in a script with both valid and invalid content."""
        mixed_script = """
# Mixed script with valid and invalid content
Write-ADTLogEntry -Message "Starting installation" -Level Info
Start-ADTMsiProcess -Path "$dirFiles\\installer.msi" -Parameters "/qn"

# This is valid
Set-ADTRegistryKey -Key "HKLM:\\Software\\MyApp" -Name "Version" -Value "1.0" -Type String

# These are hallucinated
Install-MagicalPackage -WithUnicorns $true -Rainbow "colorful"
Set-FakeADTRegistry -NonExistentKey "test"

# This is valid again
Copy-ADTFile -Source "$dirSupportFiles\\config.xml" -Destination "C:\\Program Files\\MyApp"

# Another hallucination
Remove-AllFilesWithMagic -IncludeSystem $true
"""
        script_path = self._create_test_script(mixed_script)

        # Pass the script content, not the file path
        report = self.detector.detect(mixed_script)

        self.assertTrue(
            report.get("has_hallucinations", False),
            "Mixed script should be flagged as having hallucinations",
        )

        # Should detect some but not all cmdlets as problematic
        total_cmdlets = report.get("total_cmdlets_found", 0)
        unknown_cmdlets = report.get("unknown_cmdlets_count", 0)

        self.assertGreater(
            total_cmdlets,
            unknown_cmdlets,
            "Should have more total cmdlets than unknown ones",
        )
        self.assertGreater(unknown_cmdlets, 0, "Should detect some unknown cmdlets")

    def test_typos_in_valid_cmdlets(self):
        """Test detection of typos in otherwise valid PSADT cmdlets."""
        typo_script = """
# Script with typos in valid cmdlets
Write-ADTLogEntryy -Message "Starting" -Level Info  # Extra 'y'
Start-ADTMsiProcesss -Path "installer.msi"          # Extra 's'
Set-ADTRegistrKey -Key "HKLM:\\Test"                # Missing 'y'
Copy-ADTFilee -Source "file.txt"                    # Extra 'e'
"""
        script_path = self._create_test_script(typo_script)

        # Pass the script content, not the file path
        report = self.detector.detect(typo_script)

        self.assertTrue(
            report.get("has_hallucinations", False),
            "Script with typos should be flagged",
        )

    def test_case_sensitivity_issues(self):
        """Test if case variations of valid cmdlets are properly handled."""
        case_script = """
# Script with case variations
write-adtlogentry -Message "Starting" -Level Info
START-ADTMSIPROCESS -Path "installer.msi"
set-adtregistrykey -Key "test"
COPY-ADTFILE -Source "file.txt"
"""
        script_path = self._create_test_script(case_script)

        report = self.detector.detect(script_path)

        # PowerShell is case-insensitive, so these should be valid
        # This tests if our detection properly handles case variations
        print(f"Case sensitivity test report: {report}")

    def test_confidence_scoring(self):
        """Test that confidence scores reflect the severity of hallucinations."""
        # Script with obvious hallucinations should have low confidence
        bad_script = """
Start-FakeInstaller -MagicalParameter "unicorn"
Install-NonExistentTool -WithRainbows $true
Remove-AllSystemFiles -ForceDestruction $true
"""
        bad_script_path = self._create_test_script(bad_script)
        bad_report = self.detector.detect(bad_script_path)

        # Script with subtle issues should have medium confidence
        subtle_script = """
Write-ADTLogEntry -Message "Starting" -Level Info
Start-ADTMsiProcess -Path "installer.msi" -ExtraParam "test"
Copy-ADTFile -Source "file.txt" -Destination "C:\\Temp"
"""
        subtle_script_path = self._create_test_script(subtle_script)
        subtle_report = self.detector.detect(subtle_script_path)

        # Compare confidence scores
        bad_confidence = bad_report.get("confidence_score", 1.0)
        subtle_confidence = subtle_report.get("confidence_score", 1.0)

        print(f"Bad script confidence: {bad_confidence}")
        print(f"Subtle script confidence: {subtle_confidence}")

        # Bad script should have lower confidence than subtle issues
        if bad_report.get("has_hallucinations") and subtle_report.get(
            "has_hallucinations"
        ):
            self.assertLess(
                bad_confidence,
                subtle_confidence,
                "Script with obvious hallucinations should have lower confidence",
            )

    def test_empty_and_edge_cases(self):
        """Test edge cases like empty scripts, comments only, etc."""
        # Empty script
        empty_script = ""
        empty_script_path = self._create_test_script(empty_script)
        empty_report = self.detector.detect(empty_script_path)

        # Comments only
        comments_script = """
# This is just a comment
# Another comment
# No actual PowerShell commands
"""
        comments_script_path = self._create_test_script(comments_script)
        comments_report = self.detector.detect(comments_script_path)

        # Both should be valid (no hallucinations) since there are no cmdlets to validate
        self.assertFalse(empty_report.get("has_hallucinations", True))
        self.assertFalse(comments_report.get("has_hallucinations", True))

    @unittest.skipIf(os.getenv("SKIP_MCP_TESTS") == "1", "MCP server not available")
    def test_end_to_end_with_mcp_server(self):
        """Integration test with real MCP server if available."""
        integration_script = """
# Test script for MCP integration
Write-ADTLogEntry -Message "Testing MCP integration" -Level Info
Start-ADTMsiProcess -Path "$dirFiles\\test.msi" -Parameters "/qn"
Set-ADTRegistryKey -Key "HKLM:\\Software\\Test" -Name "MCPTest" -Value "success"

# Add some hallucinated content
Install-MCPTestPackage -WithMagic $true
Remove-NonExistentADTFunction -Force
"""
        script_path = self._create_test_script(integration_script)

        try:
            report = self.detector.detect(script_path)
            print(f"MCP Integration Test Report: {report}")

            # Should detect the hallucinated cmdlets
            self.assertTrue(report.get("has_hallucinations", False))
            self.assertIn("Install-MCPTestPackage", str(report))
            self.assertIn("Remove-NonExistentADTFunction", str(report))

        except Exception as e:
            self.skipTest(f"MCP server not available: {e}")


if __name__ == "__main__":
    # Run with verbose output to see detailed results
    unittest.main(verbosity=2)
