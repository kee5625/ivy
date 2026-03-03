from __future__ import annotations
from azure.cosmos import CosmosClient, ContainerProxy, PartitionKey

import os

from azure.core.exceptions import ResourceExistsError
from azure.identity import DefaultAzureCredential

DEFAULT_COSMOS_CONTAINER = "ivy-container"

def get_cosmos_container_name() -> str:
    return os.getenv("COSMOS_CONTAINER", DEFAULT_COSMOS_CONTAINER)


def create_cosmos_client() -> CosmosClient | None:
    account_url = os.getenv("COSMOS_ACCOUNT_URL")
    if not account_url:
        return None
    credential = DefaultAzureCredential()
    return CosmosClient(account_url=account_url, credential=credential)


def get_container_client(
    cosmos_client: CosmosClient,
    container_name: str | None = None,
) -> ContainerProxy:
    database_name = os.getenv("COSMOS_DATABASE", "ivy")
    database = cosmos_client.get_database_client(database_name)
    return database.get_container_client(container_name or get_cosmos_container_name())


def ensure_container_exists(container_client: ContainerProxy) -> None:
    try:
        container_client.create_container_if_not_exists(
            partition_key=PartitionKey(path="/job_id"),
        )
    except ResourceExistsError:
        return