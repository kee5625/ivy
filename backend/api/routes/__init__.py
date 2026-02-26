from fastapi import APIRouter

from api.routes.document import router as document_router
from api.routes.system import router as system_router


router = APIRouter()
router.include_router(system_router)
router.include_router(document_router)
