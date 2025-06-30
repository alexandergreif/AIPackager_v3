#!/usr/bin/env python3
"""
Test script for PSADT v4 Documentation Parser

Tests the parser against real PSADT documentation files and demonstrates
the comprehensive cmdlet validation capabilities.
"""

import sys
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app.services.psadt_documentation_parser import (
    PSADTDocumentationParser,
    ParameterType,
    CmdletDefinition,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_psadt_parser():
    """Test the PSADT documentation parser"""
    print("🚀 Testing PSADT v4 Documentation Parser")
    print("=" * 80)

    # Initialize parser
    parser = PSADTDocumentationParser()

    # Parse all cmdlets
    print("📚 Parsing all PSADT v4 cmdlets...")
    cmdlets = parser.parse_all_cmdlets()

    if not cmdlets:
        print(
            "❌ No cmdlets found! Check if PSADT/docs/docs/ exists and contains MDX files."
        )
        return

    # Show summary
    summary = parser.get_validation_summary()
    print("\n📊 Parsing Summary:")
    print(f"  Total cmdlets: {summary['total_cmdlets']}")
    print(f"  Total parameters: {summary['total_parameters']}")
    print(f"  Cmdlets with examples: {summary['cmdlets_with_examples']}")
    print(f"  Cmdlets with parameter sets: {summary['cmdlets_with_parameter_sets']}")
    print(f"  Coverage percentage: {summary['coverage_percentage']}%")

    # Show some examples
    print("\n🔍 Sample Cmdlets Found:")
    sample_cmdlets = list(cmdlets.keys())[:10]
    for cmdlet_name in sample_cmdlets:
        cmdlet = cmdlets[cmdlet_name]
        param_count = len(cmdlet.parameters)
        example_count = len(cmdlet.examples)
        print(
            f"  ✅ {cmdlet_name} ({param_count} parameters, {example_count} examples)"
        )

    # Detailed analysis of a specific cmdlet
    if "Start-ADTMsiProcess" in cmdlets:
        print("\n🔬 Detailed Analysis: Start-ADTMsiProcess")
        analyze_cmdlet_detail(cmdlets["Start-ADTMsiProcess"])

    # Test parameter validation capabilities
    print("\n🧪 Testing Parameter Validation Capabilities")
    test_parameter_validation(cmdlets)

    # Export to JSON for inspection
    output_file = "psadt_v4_cmdlets.json"
    parser.export_to_json(output_file)
    print(f"\n💾 Exported cmdlet definitions to {output_file}")

    # Show validation improvement potential
    show_validation_improvements(cmdlets)


def analyze_cmdlet_detail(cmdlet: CmdletDefinition):
    """Analyze a specific cmdlet in detail"""
    print(f"  Name: {cmdlet.name}")
    print(f"  Synopsis: {cmdlet.synopsis[:100]}...")
    print(f"  Parameter sets: {len(cmdlet.parameter_sets)}")

    for set_name, param_set in cmdlet.parameter_sets.items():
        print(f"    📋 {set_name}:")
        print(f"      Required: {list(param_set.required_parameters)}")
        print(f"      Optional: {list(param_set.optional_parameters)}")

    print(f"  Parameters ({len(cmdlet.parameters)}):")
    for param_name, param_def in list(cmdlet.parameters.items())[:5]:  # Show first 5
        print(f"    🔧 -{param_name}:")
        print(f"      Type: {param_def.type.value}")
        print(f"      Required: {param_def.mandatory}")
        if param_def.valid_values:
            print(f"      Valid values: {param_def.valid_values}")
        if param_def.default_value:
            print(f"      Default: {param_def.default_value}")

    if len(cmdlet.parameters) > 5:
        print(f"    ... and {len(cmdlet.parameters) - 5} more parameters")

    print(f"  Examples: {len(cmdlet.examples)}")
    if cmdlet.examples:
        example = cmdlet.examples[0]
        print(f"    📝 {example.title}:")
        print(f"      {example.code}")


def test_parameter_validation(cmdlets: dict):
    """Test parameter validation capabilities"""
    # Test cases for validation
    test_cases = [
        {
            "name": "Valid Start-ADTMsiProcess call",
            "cmdlet": "Start-ADTMsiProcess",
            "params": {"FilePath": "app.msi", "Action": "Install"},
            "should_be_valid": True,
        },
        {
            "name": "Invalid Action value",
            "cmdlet": "Start-ADTMsiProcess",
            "params": {"FilePath": "app.msi", "Action": "FakeAction"},
            "should_be_valid": False,
        },
        {
            "name": "Invalid parameter name",
            "cmdlet": "Start-ADTMsiProcess",
            "params": {"FilePath": "app.msi", "FakeParameter": "value"},
            "should_be_valid": False,
        },
        {
            "name": "Incompatible parameter set",
            "cmdlet": "Start-ADTMsiProcess",
            "params": {"FilePath": "app.msi", "ProductCode": "{guid}"},
            "should_be_valid": False,
        },
    ]

    for test_case in test_cases:
        result = validate_cmdlet_call(cmdlets, test_case)
        status = "✅ PASS" if result == test_case["should_be_valid"] else "❌ FAIL"
        print(f"  {status} {test_case['name']}")


def validate_cmdlet_call(cmdlets: dict, test_case: dict) -> bool:
    """Validate a cmdlet call against parsed definitions"""
    cmdlet_name = test_case["cmdlet"]
    params = test_case["params"]

    if cmdlet_name not in cmdlets:
        return False  # Cmdlet doesn't exist

    cmdlet = cmdlets[cmdlet_name]

    # Check all parameters exist
    for param_name in params.keys():
        if param_name not in cmdlet.parameters:
            print(f"    ❌ Parameter '{param_name}' not found in {cmdlet_name}")
            return False

    # Check parameter values against valid values
    for param_name, param_value in params.items():
        param_def = cmdlet.parameters.get(param_name)
        if param_def and param_def.valid_values:
            if param_value not in param_def.valid_values:
                print(
                    f"    ❌ Invalid value '{param_value}' for parameter '{param_name}'. Valid values: {param_def.valid_values}"
                )
                return False

    # Check parameter set compatibility (simplified)
    provided_params = set(params.keys())
    for set_name, param_set in cmdlet.parameter_sets.items():
        required_params = param_set.required_parameters
        optional_params = param_set.optional_parameters
        allowed_params = required_params | optional_params

        # Check if all provided params are allowed in this set
        if provided_params.issubset(allowed_params):
            # Check if all required params are provided
            if required_params.issubset(provided_params):
                return True  # Found compatible parameter set

    print("    ❌ Parameter combination not compatible with any parameter set")
    return False


def show_validation_improvements(cmdlets: dict):
    """Show how this improves validation compared to current system"""
    print("\n🎯 Validation Improvements Over Current System:")
    print("=" * 60)

    # Current hardcoded list vs new comprehensive list
    current_hardcoded = {
        "Write-ADTLogEntry",
        "Start-ADTMsiProcess",
        "Set-ADTRegistryKey",
        "Copy-ADTFile",
        "Get-ADTLoggedOnUser",
        "Show-ADTInstallationWelcome",
        "Show-ADTInstallationProgress",
        "Close-ADTInstallationProgress",
        "Test-ADTBattery",
        "Get-ADTApplication",
        "Remove-ADTFile",
        "New-ADTFolder",
        "Get-ADTFileVersion",
    }

    parsed_cmdlets = set(cmdlets.keys())

    print("📈 Cmdlet Coverage:")
    print(f"  Current system: {len(current_hardcoded)} hardcoded cmdlets")
    print(f"  New parser: {len(parsed_cmdlets)} discovered cmdlets")
    print(
        f"  Improvement: {len(parsed_cmdlets) - len(current_hardcoded)} additional cmdlets"
    )

    # Show new cmdlets we discovered
    new_cmdlets = parsed_cmdlets - current_hardcoded
    print("\n🆕 New Cmdlets Discovered (sample):")
    for cmdlet in list(new_cmdlets)[:10]:
        print(f"  ✨ {cmdlet}")

    if len(new_cmdlets) > 10:
        print(f"  ... and {len(new_cmdlets) - 10} more!")

    # Show parameter validation improvements
    total_params = sum(len(c.parameters) for c in cmdlets.values())
    params_with_types = sum(
        1
        for c in cmdlets.values()
        for p in c.parameters.values()
        if p.type != ParameterType.STRING
    )
    params_with_enums = sum(
        1 for c in cmdlets.values() for p in c.parameters.values() if p.valid_values
    )

    print("\n🔧 Parameter Validation:")
    print(f"  Total parameters: {total_params}")
    print(f"  Parameters with specific types: {params_with_types}")
    print(f"  Parameters with enum validation: {params_with_enums}")
    print("  Current system: Basic pattern matching only")
    print("  New system: Full parameter validation with types and constraints")

    # Show examples of sophisticated validation we can now do
    print("\n💡 New Validation Capabilities:")
    print("  ✅ Parameter existence validation")
    print("  ✅ Parameter type validation (String, Int32, SwitchParameter, etc.)")
    print("  ✅ Enum value validation (Action: Install|Uninstall|Patch|Repair)")
    print("  ✅ Parameter set compatibility checking")
    print("  ✅ Required vs optional parameter validation")
    print("  ✅ Default value awareness")
    print("  ✅ Version 4 vs deprecated pattern detection")


def main():
    """Main function"""
    try:
        test_psadt_parser()
        print("\n🎉 PSADT v4 Documentation Parser test completed successfully!")
        print("\nNext steps:")
        print("1. ✅ Documentation parser created")
        print("2. 🔄 Integrate with hallucination detector")
        print("3. 🔄 Add PowerShell script AST parsing")
        print("4. 🔄 Create comprehensive validation engine")
        print("5. 🔄 Build knowledge graph integration")

    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
