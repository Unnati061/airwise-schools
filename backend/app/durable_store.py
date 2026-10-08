"""DynamoDB document repository with explicit transactional compare-and-swap."""
import json
import zlib

from botocore.exceptions import ClientError

from .repair_contracts import DraftPlan


class Conflict(Exception):
    pass


class DynamoStore:
    def __init__(self, client, table):
        self.client, self.table = client, table

    def key(self, school, key):
        return {"pk": {"S": school}, "sk": {"S": key}}

    def read(self, school, key):
        result = self.client.get_item(TableName=self.table, Key=self.key(school, key), ConsistentRead=True)
        item = result.get("Item")
        return json.loads(zlib.decompress(item["document"]["B"])) if item else None

    def query(self, school, prefix):
        records, cursor = [], None
        while True:
            args = dict(TableName=self.table, KeyConditionExpression="pk = :pk AND begins_with(sk, :prefix)",
                        ExpressionAttributeValues={":pk": {"S": school}, ":prefix": {"S": prefix}},
                        ConsistentRead=True)
            if cursor:
                args["ExclusiveStartKey"] = cursor
            result = self.client.query(**args)
            records.extend(json.loads(zlib.decompress(item["document"]["B"])) for item in result["Items"])
            cursor = result.get("LastEvaluatedKey")
            if not cursor:
                return records

    def put(self, school, key, document, expected=None, create=False):
        content = zlib.compress(json.dumps(document, sort_keys=True, separators=(",", ":")).encode())
        if len(content) > 350_000:
            raise ValueError("Document exceeds bounded DynamoDB item size")
        item = {**self.key(school, key), "document": {"B": content}}
        if "etag" in document:
            item["etag"] = {"S": document["etag"]}
        action = {"TableName": self.table, "Item": item}
        if create:
            action["ConditionExpression"] = "attribute_not_exists(pk)"
        elif expected is not None:
            action.update(ConditionExpression="etag = :expected", ExpressionAttributeValues={":expected": {"S": expected}})
        return {"Put": action}

    def transact(self, actions):
        try:
            self.client.transact_write_items(TransactItems=actions)
        except ClientError as error:
            if error.response["Error"]["Code"] in ("TransactionCanceledException", "TransactionConflictException", "ConditionalCheckFailedException"):
                raise Conflict("Concurrent change or duplicate request") from None
            raise


class DynamoPlanRepository:
    """Implements the B1 save/get interface; drafts are immutable and school-scoped."""
    def __init__(self, store, school):
        self.store, self.school = store, school

    def save(self, plan: DraftPlan, audit_action=None) -> None:
        actions = [self.store.put(self.school, f"DRAFT#{plan.id}", plan.model_dump(mode="json"), create=True)]
        if audit_action:
            actions.append(audit_action)
        self.store.transact(actions)

    def get(self, plan_id: str) -> DraftPlan | None:
        record = self.store.read(self.school, f"DRAFT#{plan_id}")
        return DraftPlan.model_validate(record) if record else None
