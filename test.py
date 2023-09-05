import os
from whoosh import fields, index, qparser, query
from shutil import rmtree

class MySchema(fields.SchemaClass):
    pref_label = fields.TEXT(stored=True)
    forename_alt_labels = fields.TEXT(stored=True)
    surname_alt_labels = fields.ID(stored=True)





def search_documents(ix_, query_user, search_type):
    fuzzy_distance = 4 if search_type == "très floue" else 2
    with ix_.searcher() as searcher:
        if search_type == "exacte":
            parser = qparser.MultifieldParser(
                ["pref_label", "forename_alt_labels", "surname_alt_labels"],
                schema=searcher.schema
            )
            parsed_query = parser.parse(query_user.lower().strip())
            results = searcher.search(parsed_query)
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

def create_store(store) -> index:
    store.destroy()
    store.create()

def create_index(store, schema):
    ix = store.create_index(schema)
    return ix

def populate_index(ix_):
    writer = ix_.writer()
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



if __name__ == '__main__':
    index_dir = "./index_dir_FS"
    query_user = "jean"
    search_type = "exacte"
    from whoosh.filedb.filestore import FileStorage
    # create necessary directory
    st = FileStorage(index_dir)
    if not os.path.exists(index_dir):
        print('> create a new store')
        create_store(st)
    # create index
    try:
        exists = st.index_exists()
        print("the index exists")
        ix = st.open_index()
    except:
        print('> create a new index')
        ix = create_index(st, MySchema)
        print("populate index")
        populate_index(ix)

    # search in documents
    search_documents(ix, query_user, search_type)

    """
    if os.path.exists(index_dir):
        print("remove dir")
        rmtree(index_dir)
    # create dir
    if not os.path.exists(index_dir):
        print("create dir")
        os.mkdir(index_dir)
    # create a storage object
    storage = FileStorage(index_dir)
    # create an index object into the storage
    ix = storage.create_index(MySchema)
    print(ix)
    """

    #create_index(index_dir)
    #search_documents(index_dir, query_user, search_type)




