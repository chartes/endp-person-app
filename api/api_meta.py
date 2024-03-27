"""api_meta.py

constant with API metadata.
"""

METADATA = {
    "title": "e-NDP - API",
    "version": "0.1.0",
    "openapi_url": "/endp-person/api/openapi.json",
    "docs_url": "/endp-person/api/docs",
    "redoc_url": "/endp-person/api/redoc",
    "license_info": {
        "name": "MIT",
        "identifier": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    "swagger_ui_parameters": {"defaultModelsExpandDepth": -1},
    "openapi_tags": [
        {"name": "default"},
        {"name": "persons", "description": "Retrieve persons and their information."},
        {"name": "persons relations", "description": "Retrieve persons relations like family relationships or events."},
        {"name": "persons thesauri", "description": "Retrieve thesaurus terms (e-NDP specific vocabulary, "
                                                    "places and status) that "
                                                    "describe persons."},
    ],
    "description": """
## Person API documentation and specification for e-NDP ANR project

For more details on this project, please visit project blog: [e-NDP ANR project](https://endp.hypotheses.org/).

This API focuses on data concerning the people encountered in the chapter registers of Notre-Dame de Paris, 
which includes data relating to:

- to the **people** themselves (canons and others);
- **Events** related to these persons;
- the **family relationships** between these people;
- the **thesaurus** to describe these people (statutes, dignities, holy orders, charges and offices, choir) 
and the places associated with the people (cloister, courthouse, domain, chapel)

These data are administered from the e-NDP people database and data are available at the end of the 
[CC BY-SA 4.0 license](http://creativecommons.org/licenses/by-sa/4.0/).
        
<!--<img alt="partenaires e-NDP" src="../static/images/banner-partners-home.png" width="300px">
<img alt="anr logo" src="../static/images/ANR-logo-C.jpg" width="120px">-->

----
""",
    "routes": {
        "get_meta_person": {
            "summary": "Get a meta and db administration information utils on person for developers.",
            "description": "",
        },
        "read_root": {
            "summary": "Check if the service is available.",
            "description": "",
        },
        "search": {
            "summary": "Full-text search to retrieve persons.",
            "description": "",
        },
        "read_persons": {
            "summary": "Retrieve all available persons.",
            "description": "",
        },
        "read_person": {
            "summary": "Retrieve a person by its _endp_id.",
            "description": "",
        },
        "read_person_events": {
            "summary": "Retrieve all events related to a specific person.",
            "description": "",
        },
        "read_person_family_relationships": {
            "summary": "Retrieve all family relationships related to a specific person.",
            "description": "",
        },
        "read_person_thesauri_terms": {
            "summary": "Retrieve all available thesauri terms.",
            "description": "",
        },
        "read_person_thesaurus_term": {
            "summary": "Retrieve a specific thesaurus term by its _endp_id.",
            "description": "",
        },


    }
}
