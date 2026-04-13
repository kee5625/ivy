from fastapi import APIRouter
from api.routes import system

router = APIRouter()
router.include_router(system.router, prefix="/system")
