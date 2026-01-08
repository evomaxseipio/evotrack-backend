"""API router registration and configuration."""

from fastapi import APIRouter

# Main API router
api_router = APIRouter()

# TODO: Import and include module routers as they are implemented
# Example structure:

# from app.modules.auth.router import router as auth_router
# from app.modules.users.router import router as users_router
# from app.modules.organizations.router import router as organizations_router
# from app.modules.projects.router import router as projects_router
# from app.modules.reports.router import router as reports_router
# from app.modules.notifications.router import router as notifications_router

# api_router.include_router(
#     auth_router,
#     prefix="/auth",
#     tags=["Authentication"]
# )

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

# api_router.include_router(
#     projects_router,
#     prefix="/projects",
#     tags=["Projects"]
# )

# api_router.include_router(
#     reports_router,
#     prefix="/reports",
#     tags=["Reports"]
# )

# api_router.include_router(
#     notifications_router,
#     prefix="/notifications",
#     tags=["Notifications"]
# )
