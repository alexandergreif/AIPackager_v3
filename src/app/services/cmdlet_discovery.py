# src/app/services/cmdlet_discovery.py

import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class CmdletDiscoveryService:
    """
    Discovers available PSADT cmdlets and their descriptions from documentation files.
    Caches the result in memory to avoid repeated file I/O.
    """

    _cached_reference: Optional[List[Dict[str, str]]] = None
    _docs_path: Path = Path("PSADT/docs/docs")

    def get_cmdlet_reference(self) -> List[Dict[str, str]]:
        """
        Gets the cached cmdlet reference. If the cache is empty, it builds it.

        Returns:
            A list of dictionaries, where each dictionary contains 'name' and 'description'.
        """
        if self._cached_reference is None:
            logger.info("Cmdlet reference cache is empty. Building now...")
            self._cached_reference = self._build_reference()
        return self._cached_reference

    def refresh_cmdlet_reference(self) -> List[Dict[str, str]]:
        """
        Forces a rebuild of the cmdlet reference cache from the documentation files.

        Returns:
            The newly built list of cmdlet references.
        """
        logger.info("Forcing a refresh of the cmdlet reference cache.")
        self._cached_reference = self._build_reference()
        return self._cached_reference

    def _build_reference(self) -> List[Dict[str, str]]:
        """
        Scans the documentation directory and parses each file to extract
        the cmdlet name and its synopsis.
        """
        if not self._docs_path.is_dir():
            logger.error(
                f"PSADT documentation directory not found at: {self._docs_path}"
            )
            return []

        reference: List[Dict[str, str]] = []
        for doc_file in self._docs_path.glob("*.mdx"):
            cmdlet_name = doc_file.stem
            try:
                content = doc_file.read_text(encoding="utf-8")
                # A more robust way to find the synopsis.
                # It's typically the first paragraph after a line that contains 'On this page'.
                lines = content.splitlines()
                description = "No description available."
                try:
                    # Find the start of the main content
                    start_index = lines.index("On this page") + 1
                    # Find the first non-empty line after that
                    for i in range(start_index, len(lines)):
                        if lines[i].strip():
                            description = lines[i].strip()
                            break
                except ValueError:
                    # Fallback for files that don't match the expected structure
                    for line in lines:
                        if line.strip() and not line.strip().startswith("#"):
                            description = line.strip()
                            break

                reference.append({"name": cmdlet_name, "description": description})

            except Exception as e:
                logger.warning(
                    f"Could not parse documentation file {doc_file.name}: {e}"
                )

        logger.info(
            f"Successfully built cmdlet reference with {len(reference)} cmdlets."
        )
        return reference


# Singleton instance to be used across the application
cmdlet_discovery_service = CmdletDiscoveryService()
