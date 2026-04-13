"""Ingestion agent for processing manuscript PDFs."""

from langgraph.func import entrypoint, task


@task
def download_pdf():
    """Download PDF from blob storage."""
    pass


@task
def parse_pdf():
    """Parse PDF into chapters."""
    pass


@task
def extract_chapter_data():
    """Extract structured data from chapter text."""
    pass


@entrypoint()
def ingestion_agent():
    """Main ingestion workflow."""
    pass
