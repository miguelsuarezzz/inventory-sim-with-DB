"""
handler.py - THE REQUEST LOGIC (who is asking, what do they want, what do we save)

No Azure code in here, so it can be tested on any computer with a fake database.

Requests it understands (all to /api/simulate):
    GET                                   -> return the shared warehouse
    POST {"action":"run","days":1}        -> run 1+ days, save, return it
    POST {"action":"reset","rules":{...}} -> start over with new rules

Who is the user?  Azure Static Web Apps handles sign-in (GitHub). It adds a header
called x-ms-client-principal to every API call: a base64-encoded JSON blob with the
signed-in person's name. We can trust it because only Azure can add it.
"""
import base64
import json
import os
from datetime import datetime, timezone

from . import inventory

MAX_EVENTS = 100      # keep the last 100 log lines (keeps the document small)
MAX_RETRIES = 3       # how many times to retry if two users collide
DOC_ID = "warehouse"


class Conflict(Exception):
    """Raised by the database layer when someone else saved first."""


def get_user(header):
    """Decode the sign-in header. Returns the username, or None if not signed in."""
    if not header:
        return None
    try:
        info = json.loads(base64.b64decode(header))
        return info.get("userDetails") or None
    except Exception:
        return None


def is_allowed(user):
    """If ALLOWED_USERS is set (comma-separated names), only those people get in."""
    allowed = os.environ.get("ALLOWED_USERS", "").strip()
    if not allowed:
        return True                      # not set = any signed-in person
    names = [n.strip().lower() for n in allowed.split(",") if n.strip()]
    return user.lower() in names


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _new_doc(rules):
    return {"id": DOC_ID, "rules": rules, "state": inventory.new_state(rules),
            "events": [], "updatedBy": None, "updatedAt": None}


def _add_events(doc, messages, user):
    """Put new messages at the front of the log (newest first), trimmed to MAX_EVENTS."""
    for msg in messages:
        doc["events"].insert(0, {"t": _now(), "user": user, "msg": msg})
    doc["events"] = doc["events"][:MAX_EVENTS]
    doc["updatedBy"], doc["updatedAt"] = user, _now()


def _view(doc, user):
    """What the browser receives: the document minus Cosmos's internal _fields."""
    out = {k: v for k, v in doc.items() if not k.startswith("_")}
    out["user"] = user
    return out


def handle(method, body, principal_header, store):
    """Returns (http_status, dict_to_send_back_as_json)."""
    user = get_user(principal_header)
    if user is None:
        return 401, {"error": "Please sign in."}
    if not is_allowed(user):
        return 403, {"error": f"{user} is not on the allowed list."}

    body = body or {}

    # ---- GET: just read the shared warehouse (create it the first time) ----
    if method == "GET":
        doc, _ = store.load()
        if doc is None:
            doc = _new_doc(inventory.clean_rules({}))
            _add_events(doc, ["Warehouse created."], user)
            store.save(doc, None)
        return 200, _view(doc, user)

    # ---- POST reset: replace everything with a fresh simulation ----
    if body.get("action") == "reset":
        rules = inventory.clean_rules(body.get("rules"))
        doc = _new_doc(rules)
        _add_events(doc, [f"Reset by {user}. Each product starts with {rules['startStock']} units."], user)
        store.save(doc, None)                      # overwrite on purpose
        return 200, _view(doc, user)

    # ---- POST run: advance the days, saving safely ----
    if body.get("action") == "run":
        try:
            days = int(body.get("days", 1))
        except (TypeError, ValueError):
            days = 1
        for _ in range(MAX_RETRIES):
            doc, etag = store.load()
            if doc is None:
                doc = _new_doc(inventory.clean_rules({}))
            messages = inventory.run_days(doc["state"], doc["rules"], days)
            _add_events(doc, messages, user)
            try:
                store.save(doc, etag)
                return 200, _view(doc, user)
            except Conflict:
                continue                           # someone saved first: reload and redo
        return 409, {"error": "Someone else is updating at the same time. Try again."}

    return 400, {"error": "Unknown action."}
