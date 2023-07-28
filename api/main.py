"""
main.py

Entry point for FastAPI application.
"""
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware

from .admin import flask_app
from .routes import api_router


def create_app():
    """Create FastAPI application.
        :return: FastAPI application
        :rtype: FastAPI
        """
    # TODO: add to settings
    _app = FastAPI(
        title="e-NDP API",
        description="e-NDP API for the e-NDP project",
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
    )
    # Add routes
    _app.include_router(api_router, prefix="/api")
    # Mount admin interface (flask app) into FastAPI app
    _app.mount('/', WSGIMiddleware(flask_app))
    return _app


app = create_app()
