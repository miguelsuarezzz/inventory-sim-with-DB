"""
store.py - THE DATABASE LAYER (talks to Azure Cosmos DB)

The whole warehouse lives in ONE document in a Cosmos DB container:
    database:  inventorydb
    container: warehouse
    document id: "warehouse"
Every user reads and writes this same document, so everyone sees the same stock.

Two users clicking at the same moment: each saved document carries a hidden
version tag called an "etag". When we save, we say "only save if nobody changed
this since I read it". If someone did, Cosmos refuses and we raise Conflict, and
handler.py simply tries again. This stops one user overwriting another.

The two settings it needs (COSMOS_ENDPOINT, COSMOS_KEY) come from the Static Web
App's environment variables, never from the code (so no secrets on GitHub).
"""
import os
from azure.cosmos import CosmosClient, PartitionKey, exceptions
from azure.core import MatchConditions

from .handler import Conflict   # the error we raise when two users collide

DB_NAME = "inventorydb"
CONTAINER_NAME = "warehouse"
DOC_ID = "warehouse"


class CosmosStore:
    def __init__(self):
        client = CosmosClient(os.environ["COSMOS_ENDPOINT"], credential=os.environ["COSMOS_KEY"])
        # Create the database and container the first time (does nothing if they exist).
        # 400 RU/s is shared by the whole database and sits inside the free 1000 RU/s.
        db = client.create_database_if_not_exists(DB_NAME, offer_throughput=400)
        self.container = db.create_container_if_not_exists(
            id=CONTAINER_NAME, partition_key=PartitionKey(path="/id"))

    def load(self):
        """Return (document, etag), or (None, None) if nothing is saved yet."""
        try:
            item = self.container.read_item(DOC_ID, partition_key=DOC_ID)
        except exceptions.CosmosResourceNotFoundError:
            return None, None
        return item, item["_etag"]

    def save(self, doc, etag):
        """Save the document. With an etag: only if unchanged. Without: overwrite."""
        if etag is None:
            self.container.upsert_item(doc)
            return
        try:
            self.container.replace_item(item=DOC_ID, body=doc, etag=etag,
                                        match_condition=MatchConditions.IfNotModified)
        except exceptions.CosmosAccessConditionFailedError:
            raise Conflict()
