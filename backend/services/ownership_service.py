def readable_owner_scope(user, table_alias=None):
    column = f"{table_alias}.user_id" if table_alias else "user_id"
    if user:
        return f"({column} IS NULL OR {column} = %s)", [user["id"]]
    return f"{column} IS NULL", []


def editable_owner_scope(user, table_alias=None):
    column = f"{table_alias}.user_id" if table_alias else "user_id"
    return f"{column} = %s", [user["id"]]


def mark_manageable(records, user):
    for record in records:
        owner_id = record.pop("user_id", None)
        record["can_manage"] = bool(user and owner_id == user["id"])
    return records