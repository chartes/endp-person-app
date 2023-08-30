"""
main.py

Entry point for FastAPI application.
"""
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination

from .admin import flask_app
from .routes import api_router

DESCRIPTION = """
## Person API documentation and specification for e-NDP ANR project

For more details on this project, please visit project blog: [e-NDP ANR project](https://endp.hypotheses.org/).

This API focuses on data concerning the people encountered in the chapter registers of Notre-Dame de Paris, which includes data relating to:

- to the **people** themselves (canons and others);
- **Events** related to these persons;
- the **family relationships** between these people;
- the **thesaurus** to describe these people (statutes, dignities, holy orders, charges and offices, choir) 
and the places associated with the people (cloister, courthouse, domain, chapel)

These data are administered from the e-NDP people database and data are available at the end of the [CC BY-SA 4.0 license](http://creativecommons.org/licenses/by-sa/4.0/).
        
<img alt="partenaires e-NDP" src="../static/images/banner-partners-home.png" width="300px">
<img alt="anr logo" src="../static/images/ANR-logo-C.jpg" width="120px">

----
"""


def create_app():
    """Create FastAPI application.
        :return: FastAPI application
        :rtype: FastAPI
        """
    # TODO: add to settings
    _app = FastAPI(
        title="e-NDP API",
        description=DESCRIPTION,
        version="0.1.0",
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        license_info={
            "name": "MIT",
            "identifier": "MIT",
            "url": "https://opensource.org/licenses/MIT",
        },
    )
    origins = [
        "*",
        "http://localhost",
        "http://localhost:8888",
        "http://localhost:9091",
    ]
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    # extensions
    add_pagination(_app)
    # Add routes
    _app.include_router(api_router, prefix="/api")
    # Mount admin interface (flask app) into FastAPI app
    _app.mount('/', WSGIMiddleware(flask_app))
    return _app


app = create_app()
