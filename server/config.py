import os

from dotenv import load_dotenv
from gremlin_python.driver.client import Client
from gremlin_python.driver.serializer import GraphSONSerializersV2d0


load_dotenv()

FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
GREMLIN_ENDPOINT = os.getenv("GREMLIN_ENDPOINT", "")
GREMLIN_DATABASE = os.getenv("GREMLIN_DATABASE", "ivy-db")
GREMLIN_GRAPH = os.getenv("GREMLIN_GRAPH", "storygraph")
GREMLIN_KEY = os.getenv("GREMLIN_KEY", "")
PORT = os.getenv("PORT", "8000")


def get_gremlin_username(database: str, graph: str) -> str:
    return f"/dbs/{database}/colls/{graph}"


def is_gremlin_configured() -> bool:
    return bool(GREMLIN_ENDPOINT and GREMLIN_KEY)


def build_gremlin_client() -> Client:
    return Client(
        GREMLIN_ENDPOINT,
        "g",
        username=get_gremlin_username(GREMLIN_DATABASE, GREMLIN_GRAPH),
        password=GREMLIN_KEY,
        message_serializer=GraphSONSerializersV2d0(),
    )
