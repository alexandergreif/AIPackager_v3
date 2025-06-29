# run_crawler.py

import asyncio
from src.app.services.mcp_service import mcp_service

# The URL to the root of the PSADT documentation
# In a real scenario, this would point to a live URL.
# For this example, we'll use a placeholder.
PSADT_DOCS_URL = "https://all-docs.zip/main/PSADT/docs/docs"


async def main() -> None:
    print(f"Starting crawl and index for URL: {PSADT_DOCS_URL}")
    result = mcp_service.crawl_and_index(PSADT_DOCS_URL)
    print(f"Crawling completed with result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
