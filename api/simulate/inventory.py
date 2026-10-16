"""
inventory.py  -  THE SIMULATION LOGIC (pure Python, no Azure needed)

You can test this file on its own on your computer:
    python inventory.py
It prints a 7-day simulation to the screen.

Each simulated day, for every product, three things happen in order:
  1. DELIVERIES  - supplier orders due today are added to stock
  2. SALES       - random customer demand; what we can't fill is "lost"
  3. REORDERING  - if stock + already-ordered <= reorder point, order more
"""
import random

# The product list. "pop" = popularity (0 to 1). A mattress (1.0) sells
# more than a dining set (0.4). Add a line here to add a product.
CATALOG = [
    {"name": "3-piece sectional sofa", "pop": 0.6},
    {"name": "Queen bed frame",        "pop": 0.8},
    {"name": "7-piece dining set",     "pop": 0.4},
    {"name": "Leather recliner",       "pop": 0.7},
    {"name": "Queen mattress",         "pop": 1.0},
    {"name": "Coffee table",           "pop": 0.9},
]

# Default rules. The web page sends its own values, these are the fallback.
DEFAULT_RULES = {
    "startStock": 40,     # units of each product at the start
    "reorderPoint": 15,   # reorder when stock (+ on order) falls to this
    "reorderQty": 30,     # units per supplier order
    "leadTime": 3,        # days until a supplier order arrives
    "maxDemand": 8,       # max customer orders per day (before popularity)
}


def clean_rules(raw):
    """Take rules from the web page, fill gaps with defaults, force valid numbers."""
    rules = dict(DEFAULT_RULES)
    for key in rules:
        try:
            rules[key] = max(0, int((raw or {}).get(key, rules[key])))
        except (TypeError, ValueError):
            pass  # keep the default if the value isn't a number
    # These three can never be zero
    for key in ("reorderQty", "leadTime", "maxDemand"):
        rules[key] = max(1, rules[key])
    return rules


def new_state(rules):
    """Create a fresh simulation at day 0."""
    return {
        "day": 0, "sold": 0, "lost": 0, "orders": 0,
        # "pending" = supplier orders placed but not arrived, e.g. {"qty":30,"arrives":5}
        "items": [dict(c, stock=rules["startStock"], sold=0, pending=[]) for c in CATALOG],
    }


def run_day(state, rules, events):
    """Advance the simulation by one day. Changes 'state', adds text to 'events'."""
    state["day"] += 1
    today = state["day"]

    for item in state["items"]:
        # STEP 1 - DELIVERIES
        for order in [o for o in item["pending"] if o["arrives"] <= today]:
            item["stock"] += order["qty"]
            events.append(f"Day {today}: {order['qty']} {item['name']} delivered from supplier.")
        item["pending"] = [o for o in item["pending"] if o["arrives"] > today]

        # STEP 2 - CUSTOMER SALES
        # Random demand from 0 up to (max demand x popularity)
        demand = int(random.random() * rules["maxDemand"] * item["pop"] + 0.5)
        sold = min(item["stock"], demand)       # can't sell more than we have
        item["stock"] -= sold
        item["sold"] += sold
        state["sold"] += sold
        state["lost"] += demand - sold          # demand we couldn't meet
        if demand > sold:
            events.append(f"Day {today}: Out of stock: {demand - sold} {item['name']} order(s) lost.")

        # STEP 3 - REORDER CHECK
        on_order = sum(o["qty"] for o in item["pending"])
        if item["stock"] + on_order <= rules["reorderPoint"]:
            item["pending"].append({"qty": rules["reorderQty"], "arrives": today + rules["leadTime"]})
            state["orders"] += 1
            events.append(f"Day {today}: Reordered {rules['reorderQty']} {item['name']} "
                          f"(arrives day {today + rules['leadTime']}).")


def run_days(state, rules, days):
    """Run several days and return the list of events that happened."""
    events = []
    for _ in range(max(0, min(int(days), 30))):   # cap at 30 days per request
        run_day(state, rules, events)
    return events


# Lets you run:  python inventory.py   to test without Azure
if __name__ == "__main__":
    rules = clean_rules({})
    state = new_state(rules)
    for line in run_days(state, rules, 7):
        print(line)
    print(f"\nAfter {state['day']} days: sold {state['sold']}, "
          f"lost {state['lost']}, supplier orders {state['orders']}")
    for it in state["items"]:
        print(f"  {it['name']:<26} stock {it['stock']:>3}")
