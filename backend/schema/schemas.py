def individual_serial(item) -> dict:
    return {
        "id": str(item["_id"]),
        "name": str(item["name"]),
        "description": str(item["description"]),
        "complete": str(item["complete"]),
    }

def list_serial(items) -> list:
    return [individual_serial(item) for item in items]
 