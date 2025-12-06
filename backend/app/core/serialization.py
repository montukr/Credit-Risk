from bson import ObjectId

def to_str_id(doc: dict) -> dict:
    """Return a shallow copy of doc with _id and any ObjectId fields converted to str."""
    if not isinstance(doc, dict):
        return doc
    new_doc = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            new_doc[k] = str(v)
        else:
            new_doc[k] = v
    # ensure a top-level "id" key, useful for frontend
    if "_id" in new_doc and "id" not in new_doc:
        new_doc["id"] = new_doc["_id"]
    return new_doc

def to_str_id_list(docs):
    return [to_str_id(d) for d in docs]
