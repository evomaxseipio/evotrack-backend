"""API router registration and configuration."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router

# Main API router
api_router = APIRouter()

# Register auth router
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# TODO: Include other module routers as they are implemented
# from app.modules.users.router import router as users_router
# from app.modules.organizations.router import router as organizations_router
# from app.modules.projects.router import router as projects_router

# api_router.include_router(
#     users_router,
#     prefix="/users",
#     tags=["Users"]
# )

# api_router.include_router(
#     organizations_router,
#     prefix="/organizations",
#     tags=["Organizations"]
# )
