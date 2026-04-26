from fastapi import APIRouter
from api.routes import document, system, upload

router = APIRouter()
router.include_router(system.router, prefix="/system")
router.include_router(upload.router, prefix="/upload")
router.include_router(document.router, prefix="/jobs")
