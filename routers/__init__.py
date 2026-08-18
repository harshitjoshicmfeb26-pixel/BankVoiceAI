from fastapi import APIRouter
from .auth import router as auth_router
from .accounts import router as accounts_router
from .payments import router as payments_router
from .chat import router as chat_router
from .document import router as document_router

router = APIRouter()

router.include_router(auth_router)
router.include_router(accounts_router)
router.include_router(payments_router)
router.include_router(chat_router)
router.include_router(document_router)
