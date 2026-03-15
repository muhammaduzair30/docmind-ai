from fastapi import APIRouter 

#import route modules
from app.api.v1.routes import upload
from app.api.v1.routes import query
from app.api.v1.routes import auth
from app.api.v1.routes import documents

# create main API router
api_router = APIRouter()

#include all route modules
api_router.include_router(upload.router, prefix="/upload", tags=["Upload"])
api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(documents.router, prefix="/documents", tags=["Documents"])
api_router.include_router(auth.router)
