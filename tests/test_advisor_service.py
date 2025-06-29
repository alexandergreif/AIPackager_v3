import pytest
from src.app.services.advisor_service import AdvisorService
from src.app.schemas import PSADTScript


@pytest.fixture
def advisor():
    return AdvisorService()


def test_advisor_service_no_correction_needed(advisor):
    """Test that the advisor service makes no changes when the script is clean."""
    clean_script = PSADTScript(
        pre_installation_tasks=["Show-ADTInstallationWelcome"],
        installation_tasks=["Start-ADTMsiProcess -Action Install"],
        post_installation_tasks=[],
        uninstallation_tasks=["Start-ADTMsiProcess -Action Uninstall"],
        post_uninstallation_tasks=[],
    )
    hallucination_report = {"has_hallucinations": False, "issues": []}

    corrected_script = advisor.correct_script(clean_script, hallucination_report)

    assert corrected_script == clean_script
    assert not corrected_script.corrections_applied


def test_advisor_service_removes_unknown_cmdlet(advisor):
    """Test that the advisor service removes an unknown cmdlet."""
    script_with_hallucination = PSADTScript(
        pre_installation_tasks=["Show-ADTInstallationWelcome"],
        installation_tasks=["Start-ADTMsiProcess -Action Install", "Fake-Command"],
        post_installation_tasks=[],
        uninstallation_tasks=["Start-ADTMsiProcess -Action Uninstall"],
        post_uninstallation_tasks=[],
    )
    hallucination_report = {
        "has_hallucinations": True,
        "issues": [{"type": "unknown_cmdlets", "cmdlets": ["Fake-Command"]}],
    }

    corrected_script = advisor.correct_script(
        script_with_hallucination, hallucination_report
    )

    assert "Fake-Command" not in corrected_script.installation_tasks
    assert corrected_script.corrections_applied
    assert (
        "Removed unknown cmdlet: Fake-Command"
        in corrected_script.corrections_applied[0]
    )


def test_advisor_service_handles_empty_script(advisor):
    """Test that the advisor service handles an empty script gracefully."""
    empty_script = PSADTScript(
        pre_installation_tasks=[],
        installation_tasks=[],
        post_installation_tasks=[],
        uninstallation_tasks=[],
        post_uninstallation_tasks=[],
    )
    hallucination_report = {"has_hallucinations": False, "issues": []}

    corrected_script = advisor.correct_script(empty_script, hallucination_report)

    assert corrected_script == empty_script
    assert not corrected_script.corrections_applied
