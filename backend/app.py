import asyncio
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from azure.cosmos.aio import CosmosClient
from azure.cosmos import PartitionKey, exceptions
from dotenv import dotenv_values

# Logger
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


config = dotenv_values(".env")
DB_NAME="todo-db"
CONTAINER_NAME="todo-items"

# FASTAPI app
app = FastAPI(title="ivy")
app.add_middleware(
    CORSMiddleware,  # type: ignore[ arg-type ]
    allow_origins=[config["FRONTEND_ORIGIN"]],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def _log_task_exception(task: "asyncio.Task[None]", job_id: str) -> None:
    try:
        task.result()
    except Exception:
        logger.exception("[job:%s] Indexing job failed", job_id)

@app.on_event("startup")
async def startup_db_client():
    app.cosmos_client = CosmosClient(config["URI"], credential = config["KEY"])
    await get_or_create_db(DB_NAME)
    await get_or_create_container(CONTAINER_NAME)

async def get_or_create_db(db_name):
    try:
        app.database = app.cosmos_client.get_database_client(db_name)
        return await app.database.read()
    except exceptions.CosmosResourceNotFoundError:
        print("Creating Database")
        return await app.cosmos_client.create_database(db_name)
        
async def get_or_create_container(container_name):
    try:        
        app.todo_items_container = app.database.get_container_client(container_name)
        return await app.todo_items_container.read()   
    except exceptions.CosmosResourceNotFoundError:
        print("Creating container with id as partition key")
        return await app.database.create_container(id=container_name, partition_key=PartitionKey(path="/id"))
    except exceptions.CosmosHttpResponseError:
        raise

if __name__ == "__main__":
    import uvicorn

    try:
        port_value = int(config["PORT"]) if config["PORT"] is not None else 8000
    except ValueError:
        port_value = 8000
    uvicorn.run(app, host="0.0.0.0", port=port_value)
