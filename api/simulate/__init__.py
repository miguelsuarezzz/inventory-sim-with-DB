"""
__init__.py - THE AZURE FUNCTION (thin wrapper)

Azure calls main() for every request to /api/simulate. It passes the request
details to handler.handle() and turns the answer into an HTTP response.
"""
import json
import logging
import azure.functions as func

from . import handler

_store = None   # created once, then reused while the function stays warm


def _reply(status, payload):
    return func.HttpResponse(json.dumps(payload), status_code=status, mimetype="application/json")


def main(req: func.HttpRequest) -> func.HttpResponse:
    global _store
    try:
        if _store is None:
            from . import store            # imported here so a missing package gives a clear error
            _store = store.CosmosStore()
        body = {}
        if req.method == "POST":
            try:
                body = req.get_json()
            except ValueError:
                return _reply(400, {"error": "Send JSON."})
        status, payload = handler.handle(
            req.method, body, req.headers.get("x-ms-client-principal"), _store)
        return _reply(status, payload)
    except KeyError as err:
        logging.exception("Missing setting")
        return _reply(500, {"error": f"Missing app setting {err}. Add COSMOS_ENDPOINT and COSMOS_KEY."})
    except Exception:
        logging.exception("Unexpected error")
        return _reply(500, {"error": "Server error. Check the function logs in Azure."})
