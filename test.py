import os
from whoosh import fields, index, qparser, query


class MySchema(fields.SchemaClass):
    pref_label = fields.TEXT(stored=True)
    forename_alt_labels = fields.TEXT(stored=True)
    surname_alt_labels = fields.ID(stored=True)


def create_index(index_dir):
    if not os.path.exists(index_dir):
        os.mkdir(index_dir)

    my_index = index.create_in(index_dir, MySchema)
    writer = my_index.writer()
    writer.add_document(pref_label=u"Guillaume Aleaume oncle de Jean Morain",
                        forename_alt_labels=u"Guillelmus; Guillermus; Guillaume",
                        surname_alt_labels=u"Aleaume")
    writer.add_document(pref_label=u"Simon Alégret",
                        forename_alt_labels=u"Symon; Simon ; Symo ; Johannes",
                        surname_alt_labels=u"Alegreti; Allegreti; Algreti; Halegreti")
    writer.add_document(pref_label=u"Jean Alegrin",
                        forename_alt_labels=u"Johannes; Jehan",
                        surname_alt_labels=u"Alegrin")
    writer.add_document(pref_label=u"Guillaume d’Auge neveu de Jean Le Moustardier",
                        forename_alt_labels=u"Guillelmus; Guillermus; Guillaume",
                        surname_alt_labels=u"Algia de; Dauge; Auge de; Auge d’")
    writer.add_document(pref_label=u"Jean Morain",
                        forename_alt_labels=u"Guillelmus; Guillermus; Guillaume",
                        surname_alt_labels=u"Algia de; Plaisans avant d’")
    # Ajoutez d'autres documents ici
    writer.commit()


def search_documents(index_dir, query_user, search_type):
    fuzzy_distance = 4 if search_type == "très floue" else 2
    print(query_user)
    with index.open_dir(index_dir).searcher() as searcher:
        print(query_user)
        if search_type == "exacte":
            parser = qparser.MultifieldParser(
                ["pref_label", "forename_alt_labels", "surname_alt_labels"],
                schema=searcher.schema
            )
            print(parser)
            parsed_query = parser.parse(query_user.lower().strip())
            print(parsed_query)
            results = searcher.search(parsed_query)
            print(results)
        else:
            terms = query_user.split()
            term_objs = [
                query.Or(
                    [
                        query.FuzzyTerm(fieldname, term, maxdist=fuzzy_distance)
                        for fieldname in ["pref_label", "forename_alt_labels", "surname_alt_labels"]
                    ]
                )
                for term in terms
            ]
            fuzzy_query = query.Or(term_objs)
            results = searcher.search(fuzzy_query)

        search_results = [{"pref_label": hit["pref_label"]} for hit in results]
        for result in search_results:
            print(result)


if __name__ == '__main__':
    index_dir = "./index_dir"
    query_user = "jean"
    search_type = "exacte"

    create_index(index_dir)
    search_documents(index_dir, query_user, search_type)




