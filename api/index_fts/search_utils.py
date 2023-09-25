"""search_utils.py

Whoosh search utils for searching indexes.
"""

from whoosh import (query,
                    qparser,
                    index)

fuzzy_ratio = {
    "fuzzy": 2,
    "very_fuzzy": 4
}


def search_index(ix: index,
                 query_user: str,
                 search_type: str,
                 fieldnames: list,
                 limit: int = 20,
                 ) -> list:
    with ix.searcher() as searcher:
        if search_type == "exact":
            parser = qparser.MultifieldParser(
                fieldnames,
                schema=searcher.schema
            )
            parsed_query = parser.parse(query_user.lower().strip())
            results = [{"id": result['id'],
                        "_id_endp": result['id_endp']}
                       for result in searcher.search(parsed_query)]
        else:
            fuzzy_distance = fuzzy_ratio[search_type]
            term_objs = [
                query.Or(
                    [
                        query.FuzzyTerm(field_name, term, maxdist=fuzzy_distance)
                        for field_name in fieldnames
                    ]
                )
                for term in query_user.lower().strip().split()
            ]
            parsed_query = query.Or(term_objs)
            results = [{"id": result['id'],
                    "_id_endp": result['id_endp']}
                   for result in searcher.search(parsed_query, limit=limit)]
    return results
