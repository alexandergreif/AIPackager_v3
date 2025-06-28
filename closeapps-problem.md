# Summary of the `-CloseApps` Issue

**Last Updated**: 2025-06-27

## 1. The Core Problem

The generated PSADT script does not correctly identify the process executable name to close during the pre-installation phase. It defaults to using the full application `ProductName` from the metadata, which is incorrect.

**Incorrect Behavior:**
```powershell
Show-ADTInstallationWelcome -CloseProcesses @{ Name = 'Google Chrome Installer'; ... }
```

**Expected Behavior:**
```powershell
Show-ADTInstallationWelcome -CloseApps 'chrome.exe' ...
```

This happens because the deterministic method of extracting the executable name from the MSI file is failing, and there is no fallback mechanism.

## 2. Root Cause Analysis

The terminal and application logs have consistently shown that the `msiinfo` command-line tool, used to extract metadata from MSI files, is failing to retrieve executable names.

-   **Initial Log Evidence**: `Could not extract executables from MSI table 'Icon': Command '['msiinfo', ...]' returned non-zero exit status 1.`
-   **Manual Debugging - `Property` Table**: Running `msiinfo export <msi_path> Property` directly in the terminal *succeeded*, indicating `msitools` is installed and functional for some tables.
-   **Manual Debugging - `_Tables` Table**: Running `msiinfo export <msi_path> _Tables` successfully listed all tables, confirming `File` and `Icon` tables exist, but `Shortcut` does not.
-   **Manual Debugging - `Shortcut` Table**: Running `msiinfo export <msi_path> Shortcut` directly in the terminal failed with `table not found`, confirming this table is absent in the Google Chrome MSI.
-   **Manual Debugging - `Icon` Table**: Running `msiinfo export <msi_path> Icon` directly in the terminal also failed with `table not found` (similar to Shortcut), indicating this table is also absent or inaccessible in this specific MSI.
-   **Manual Debugging - `File` Table**: Running `msiinfo export <msi_path> File` directly in the terminal *succeeded* in exporting the table structure, but showed no data rows for executables. This suggests the `File` table might be empty of relevant executables, or its format is not what we expected for direct executable names.

**Conclusion**: The deterministic approach of extracting executable names from MSI tables (`Icon`, `Shortcut`, `File`) is proving unreliable for the Google Chrome MSI, as these tables either do not exist or do not contain the expected executable data.

## 3. Key Involved Files

The following files are central to this problem and its solution:

-   **`src/app/metadata_extractor.py`**: This service is responsible for calling `msiinfo` and extracting all metadata, including the executable names. We have attempted to fix its `subprocess.run` calls to capture `stdout` directly.
-   **`src/app/models.py`**: Defines the database schema. We have already added the `executable_names: Mapped[Optional[list]] = mapped_column(JSON)` field to the `Metadata` table.
-   **`src/app/routes.py`**: The main workflow orchestrator. It calls the metadata extractor and saves the results to the database.
-   **`src/app/templates/psadt/Invoke-AppDeployToolkit.ps1.j2`**: The final script template. It contains the `if/else` logic to use `-CloseApps` if `executable_names` is available, or fall back to `-CloseProcesses`.
-   **`src/app/schemas.py`**: Will need modification to add a field for AI-predicted processes.
-   **`src/app/prompts/instruction_processing.j2`**: Will need modification to instruct the AI to predict process names.
-   **`src/app/services/instruction_processor.py`**: Will need modification to handle AI-predicted processes.

## 4. Proposed Next Steps (for tomorrow)

Given the unreliability of deterministic MSI parsing for executable names, the most robust and reliable path forward is to implement the AI-powered fallback mechanism.

1.  **Implement the AI Fallback (Hybrid Approach)**:
    *   **Action**: Implement the AI-powered prediction as the primary method for identifying process names, as the deterministic MSI check is proving unreliable for common installers like Google Chrome.
    *   **Steps**:
        1.  Modify the `InstructionResult` schema in `src/app/schemas.py` to include a `predicted_processes_to_close: Optional[List[str]]` field.
        2.  Enhance the `instruction_processing.j2` prompt to explicitly ask the AI to predict the process names based on the application's `ProductName` and `filename`.
        3.  Update the `InstructionProcessor` to parse this new field from the AI's response.
        4.  In `routes.py`, after the metadata extraction step, check if `executable_names` (from MSI parsing) is empty. If it is, take the `predicted_processes_to_close` from the `InstructionResult` (which is generated in Stage 1 of the pipeline) and save those to the `executable_names` field in the database instead.

This summary provides a clear and complete context for tackling the problem with a fresh start, focusing on the most reliable solution given our findings.
