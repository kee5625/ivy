import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gremlin_python.driver.client import Client
from integrations.azure.openai_client import get_openai_client

from api import router as api_router
from config import (
    FRONTEND_ORIGIN,
    GREMLIN_DATABASE,
    GREMLIN_GRAPH,
    PORT,
    build_gremlin_client,
    is_gremlin_configured,
)


logging.basicConfig(level=logging.DEBUG, format="%(levelname)-8s %(name)s: %(message)s")
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI(title="ivy")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    @app.on_event("startup")
    async def startup_gremlin_client() -> None:
        openai_client = get_openai_client()
        if openai_client is None:
            logger.warning(
                "OpenAI client not configured. "
                "Set OPENAI_ENDPOINT + PROJECT_KEY (direct) "
                "or PROJECT_ENDPOINT (Foundry)."
            )
        else:
            logger.info("OpenAI client initialised.")
        app.state.openai_client = openai_client
        if not is_gremlin_configured():
            logger.warning(
                "Gremlin not configured. Set GREMLIN_ENDPOINT and GREMLIN_KEY."
            )
            app.state.gremlin_client = None
            return

        app.state.gremlin_client = build_gremlin_client()
        logger.info(
            "Gremlin client initialized for db=%s graph=%s",
            GREMLIN_DATABASE,
            GREMLIN_GRAPH,
        )

    @app.on_event("shutdown")
    async def shutdown_gremlin_client() -> None:
        gremlin_client: Client | None = getattr(app.state, "gremlin_client", None)
        if gremlin_client is not None:
            gremlin_client.close()
            logger.info("Closed Gremlin client connection")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    try:
        port_value = int(PORT)
    except ValueError:
        port_value = 8000

    uvicorn.run(app, host="0.0.0.0", port=port_value)
