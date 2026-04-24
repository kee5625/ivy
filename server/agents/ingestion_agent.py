"""Ingestion agent for processing manuscript PDFs."""

from langgraph.func import entrypoint, task

from utils.storage import download_pdf as fetch_pdf_bytes


@task
def download_pdf(object_key: str) -> bytes:
    """Download PDF bytes from R2."""
    return fetch_pdf_bytes(object_key)


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
