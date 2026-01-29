"""API router registration and configuration."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.auth.activation import router as activation_router
from app.modules.organizations.router import router as organizations_router
from app.modules.organizations.users_router import router as org_users_router
from app.modules.users.router import router as users_router
from app.modules.departments.router import router as departments_router
from app.modules.teams.router import router as teams_router

# Main API router
api_router = APIRouter()

# Register auth router
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"]
)

# Register activation router (public endpoints)
api_router.include_router(
    activation_router,
    prefix="/auth",
    tags=["Account Activation"]
)

# Register organizations router
api_router.include_router(
    organizations_router,
    prefix="/organizations",
    tags=["Organizations"]
)

# Register organization users router (admin)
api_router.include_router(
    org_users_router,
    prefix="",  # Routes already have /organizations/{id}/users
    tags=["Organization Users"]
)

# Register users router (profile)
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["User Profile"]
)

# Register departments router
api_router.include_router(
    departments_router,
    tags=["Departments"]
)

# Register teams router
api_router.include_router(
    teams_router,
    tags=["Teams"]
)
