import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from gremlin_python.driver.client import Client
from integrations.azure.openai_client import close_openai_client, get_openai_client

from api import router as api_router
from config import (
    FRONTEND_ORIGIN,
    GREMLIN_DATABASE,
    GREMLIN_GRAPH,
    PORT,
    build_gremlin_client,
    is_gremlin_configured,
)


# ── Logging setup ─────────────────────────────────────────────────────────────
# Root logger at INFO with a compact format — no headers, no request bodies.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s  %(name)s  %(message)s",
    datefmt="%H:%M:%S",
)

# Silence the chatty third-party loggers that dump full HTTP headers/bodies
for _noisy in (
    "azure",                     # azure-core, azure-cosmos, azure-storage, azure-identity
    "azure.core.pipeline",       # full request/response traces
    "azure.identity",            # token acquisition chatter
    "httpx",                     # request lines + headers
    "httpcore",                  # low-level connection logs
    "openai",                    # OpenAI SDK internals
    "urllib3",                   # connection pool noise
    "uvicorn.access",            # per-request access log (FastAPI already logs routes)
    "uvicorn.error",             # startup/shutdown only — keep at WARNING
    "websockets",                # gremlin websocket chatter
    "gremlinpython",             # gremlin driver internals
    "charset_normalizer",        # encoding detection noise
    "msal",                      # MSAL token cache logs
):
    logging.getLogger(_noisy).setLevel(logging.WARNING)

# Keep uvicorn's lifespan messages (startup/shutdown) visible
logging.getLogger("uvicorn").setLevel(logging.INFO)

logger = logging.getLogger(__name__)


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
        try:
            openai_client = await get_openai_client()
        except Exception as exc:
            openai_client = None
            logger.warning(
                "Azure AI Foundry client initialization failed. "
                "Set PROJECT_KEY and OPENAI_ENDPOINT (or PROJECT_ENDPOINT). "
                "Error: %s",
                exc,
            )
        else:
            if openai_client is None:
                logger.warning(
                    "Azure AI Foundry client not configured. "
                    "Set PROJECT_KEY and OPENAI_ENDPOINT (or PROJECT_ENDPOINT)."
                )
            else:
                logger.info("Azure AI Foundry client initialised.")
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
        await close_openai_client()
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
