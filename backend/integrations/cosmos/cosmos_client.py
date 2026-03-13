from __future__ import annotations

import os

from azure.core.exceptions import ResourceExistsError
from azure.cosmos import ContainerProxy, CosmosClient, PartitionKey

DEFAULT_COSMOS_CONTAINER = "ivy-container"

# Global cache to prevent connection pool exhaustion / port leaks
_cosmos_client: CosmosClient | None = None
_container_client: ContainerProxy | None = None


def get_cosmos_container_name() -> str:
    return os.getenv("COSMOS_CONTAINER", DEFAULT_COSMOS_CONTAINER)


def create_cosmos_client() -> CosmosClient | None:
    global _cosmos_client
    if _cosmos_client is not None:
        return _cosmos_client

    account_url = os.getenv("COSMOS_ACCOUNT_URL")
    if not account_url:
        return None

    key = os.getenv("COSMOS_KEY")
    if key:
        # Simplest auth: account key — works locally without any Azure CLI
        # login or managed identity configured.
        _cosmos_client = CosmosClient(url=account_url, credential=key)
        return _cosmos_client

    # Fallback for deployed environments: managed identity / Azure CLI / etc.
    from azure.identity import DefaultAzureCredential  # lazy import
    _cosmos_client = CosmosClient(url=account_url, credential=DefaultAzureCredential())
    return _cosmos_client


def get_container_client(
    cosmos_client: CosmosClient,
    container_name: str | None = None,
) -> ContainerProxy:
    global _container_client
    if _container_client is not None:
        return _container_client

    database_name = os.getenv("COSMOS_DATABASE", "ivy")
    container_name = container_name or get_cosmos_container_name()

    database = cosmos_client.get_database_client(database_name)

    # create_container_if_not_exists belongs to DatabaseProxy, not ContainerProxy
    try:
        database.create_container_if_not_exists(
            id=container_name,
            partition_key=PartitionKey(path="/job_id"),
        )
    except ResourceExistsError:
        pass

    _container_client = database.get_container_client(container_name)
    return _container_client


def ensure_container_exists(container_client: ContainerProxy) -> None:
    # No-op: container creation now happens inside get_container_client so
    # callers that pass a ContainerProxy here don't need to do anything extra.
    pass
