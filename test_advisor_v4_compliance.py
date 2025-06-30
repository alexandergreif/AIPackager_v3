#!/usr/bin/env python3
"""
Test Advisor Service PSADT v4 Compliance

Verifies that the enhanced advisor service uses only PSADT v4 cmdlets
and never falls back to v3 cmdlets when making corrections.
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.services.advisor_service import AdvisorService
from src.app.schemas import PSADTScript


def test_advisor_v4_compliance():
    """Test that advisor service uses only PSADT v4 cmdlets"""
    print("🚀 Testing Advisor Service PSADT v4 Compliance")
    print("=" * 80)

    # Initialize advisor service
    advisor = AdvisorService()

    # Check if PSADT cmdlets loaded
    cmdlet_count = len(advisor.psadt_cmdlets) if advisor.psadt_cmdlets else 0
    print(f"📚 PSADT v4 cmdlets loaded: {cmdlet_count}")

    if cmdlet_count == 0:
        print("❌ No PSADT cmdlets loaded - cannot test properly")
        return False

    # Note: Script with parameter issues will be tested via hallucination report

    # Create hallucination report similar to the one from the log
    hallucination_report = {
        "has_hallucinations": True,
        "confidence_score": 0.0,
        "issues": [
            {
                "type": "invalid_parameter",
                "description": "Parameter '-Level' not found in cmdlet 'Write-ADTLogEntry'",
                "severity": "high",
                "cmdlet": "Write-ADTLogEntry",
                "parameter": "Level",
                "suggestions": [],
            },
            {
                "type": "invalid_parameter",
                "description": "Parameter '-Parameters' not found in cmdlet 'Start-ADTProcess'",
                "severity": "high",
                "cmdlet": "Start-ADTProcess",
                "parameter": "Parameters",
                "suggestions": [],
            },
            {
                "type": "invalid_parameter",
                "description": "Parameter '-Wait' not found in cmdlet 'Start-ADTProcess'",
                "severity": "high",
                "cmdlet": "Start-ADTProcess",
                "parameter": "Wait",
                "suggestions": [],
            },
            {
                "type": "invalid_parameter",
                "description": "Parameter '-PathSource' not found in cmdlet 'Copy-ADTFile'",
                "severity": "high",
                "cmdlet": "Copy-ADTFile",
                "parameter": "PathSource",
                "suggestions": [],
            },
            {
                "type": "invalid_parameter",
                "description": "Parameter '-PathDestination' not found in cmdlet 'Copy-ADTFile'",
                "severity": "high",
                "cmdlet": "Copy-ADTFile",
                "parameter": "PathDestination",
                "suggestions": [],
            },
        ],
    }

    print("🔍 Testing PSADT v4 Reference Generation:")
    print("-" * 50)

    # Test the v4 reference generation
    v4_reference = advisor._build_psadt_v4_reference(hallucination_report)

    print("📋 Generated Reference (first 1000 chars):")
    print(v4_reference[:1000] + "..." if len(v4_reference) > 1000 else v4_reference)
    print()

    # Verify the reference contains v4 guidance
    v4_checks = [
        ("v4 cmdlets emphasis", "PSADT v4 cmdlets" in v4_reference),
        ("ADT- prefix requirement", "ADT- prefix" in v4_reference),
        ("v3 to v4 mappings", "Execute-Process → Start-ADTProcess" in v4_reference),
        ("Write-Log mapping", "Write-Log → Write-ADTLogEntry" in v4_reference),
        ("No fallback warning", "no fallback to v3" in v4_reference.lower()),
        ("Cmdlet compliance", "v4 compliance" in v4_reference.lower()),
    ]

    print("✅ Reference Quality Checks:")
    all_passed = True
    for check_name, result in v4_checks:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    print()

    # Check specific cmdlet information
    if advisor.psadt_cmdlets:
        print("📖 Cmdlet Information Available:")
        for cmdlet in ["Write-ADTLogEntry", "Start-ADTProcess", "Copy-ADTFile"]:
            if cmdlet in advisor.psadt_cmdlets:
                cmdlet_def = advisor.psadt_cmdlets[cmdlet]
                param_count = len(cmdlet_def.parameters)
                print(f"  ✅ {cmdlet}: {param_count} parameters defined")
            else:
                print(f"  ❌ {cmdlet}: Not found in database")
                all_passed = False

    print()
    print("🎯 V4 Compliance Summary:")
    if all_passed:
        print("  ✅ All checks passed - Advisor service should use PSADT v4 cmdlets")
        print("  ✅ Comprehensive reference generated with v4 guidance")
        print("  ✅ Clear warnings against v3 fallback included")
    else:
        print("  ❌ Some checks failed - Advisor may still fall back to v3")

    return all_passed


def main():
    """Main function"""
    try:
        success = test_advisor_v4_compliance()

        if success:
            print("\n🎉 Advisor Service V4 Compliance Test: SUCCESS!")
            print(
                "The enhanced advisor service is properly configured to use only PSADT v4 cmdlets."
            )
        else:
            print("\n❌ Advisor Service V4 Compliance Test: FAILED!")
            print("The advisor service may still fall back to v3 cmdlets.")

        return 0 if success else 1

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
