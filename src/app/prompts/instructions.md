# AI Agent Instructions for PSADT Script Generation

## Purpose
This document outlines the operational workflow for the AI agent responsible for generating PowerShell App Deployment Toolkit (PSADT) scripts. The primary goal is to take a user-uploaded installer (MSI/EXE) and produce a correct, high-quality, and production-ready PSADT script.

## Core Workflow

1.  **Installer Analysis:**
    *   Receive the path to the user-uploaded installer file.
    *   Extract metadata from the installer (e.g., ProductName, ProductVersion, Manufacturer). Use appropriate tools for MSI and EXE files.

2.  **Knowledge Base Query (RAG):**
    *   Formulate a query based on the installer's metadata.
    *   Use the `perform_rag_query` tool to search the PSADT knowledge base for general guidance and best practices related to the application.
    *   Use the `search_code_examples` tool to find specific PSADT code snippets and implementation patterns relevant to the application or installer type.

3.  **Script Generation:**
    *   Synthesize the information from the installer analysis and the RAG results.
    *   Generate a complete PSADT script using the retrieved context and examples.
    *   Ensure the script adheres to the PSADT best practices and the project's coding standards.

4.  **Validation (Hallucination Detection):**
    *   Save the generated script to a temporary file.
    *   Use the `check_ai_script_hallucinations` tool, providing the path to the temporary script. This will validate all PSADT cmdlets, functions, and their parameters against the official PSADT knowledge graph.
    *   If hallucinations are detected, analyze the report, revise the script to correct the errors, and re-run the validation.
    *   Repeat this process until the script passes validation with no hallucinations.

5.  **Final Output:**
    *   Once the script is validated, present the final, clean script to the user.

## Tool Usage Reference

*   **`perform_rag_query`**: Use for general questions about PSADT usage (e.g., "how to handle registry keys," "best way to install a prerequisite").
*   **`search_code_examples`**: Use to find concrete examples of PSADT code (e.g., "example for installing .NET Framework," "PSADT script for Adobe Reader").
*   **`check_ai_script_hallucinations`**: Use as a final quality gate to ensure the generated script is syntactically correct and uses only valid PSADT commands.
