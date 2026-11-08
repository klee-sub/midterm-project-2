from ..services.faces import store


def show():
    return 200, {"status": "ok", "enrolled": len(store.people)}
