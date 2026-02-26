from __future__ import annotations

import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, ContainerClient

DEFAULT_PDF_CONTAINER = "pdfs"


def get_blob_container_name() -> str:
    return os.getenv("AZURE_BLOB_CONTAINER", DEFAULT_PDF_CONTAINER)


def is_blob_configured() -> bool:
    return bool(
        os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        or os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    )


def create_blob_service_client() -> BlobServiceClient | None:
    connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    if connection_string:
        return BlobServiceClient.from_connection_string(connection_string)

    account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
    #account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
    credential = DefaultAzureCredential()
    
    if not account_url:
        return None

    if credential:
        return BlobServiceClient(account_url=account_url, credential=credential)
    return BlobServiceClient(account_url=account_url)


def get_container_client(
    blob_service_client: BlobServiceClient,
    container_name: str | None = None,
) -> ContainerClient:
    return blob_service_client.get_container_client(
        container_name or get_blob_container_name()
    )


def ensure_container_exists(container_client: ContainerClient) -> None:
    try:
        container_client.create_container()
    except ResourceExistsError:
        return
