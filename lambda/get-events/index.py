import json
import os
import boto3
from datetime import datetime, timedelta

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    # Replaces the API Gateway cache cluster. max-age caches per browser;
    # s-maxage is for a shared cache (CDN) if this ever gets fronted by one.
    # 5min is well under the 2min dequeue cadence's practical staleness.
    "Cache-Control": "public, max-age=300, s-maxage=300",
}


def handler(event, context):
    try:
        now = datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        future = now + timedelta(weeks=2)
        
        start_date = start_of_day.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = future.strftime("%Y-%m-%dT%H:%M:%S")

        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ["DYNAMO_EVENTS_TABLE_NAME"]
        table = dynamodb.Table(table_name)

        # A scan page stops at 1MB *before* filtering, so follow LastEvaluatedKey.
        # ponytail: full table scan per request, add a GSI on event date if latency/cost bites.
        scan_kwargs = dict(
            FilterExpression="ai_data.#dt BETWEEN :start AND :end",
            ExpressionAttributeNames={"#dt": "datetime"},
            ExpressionAttributeValues={":start": start_date, ":end": end_date},
        )
        events = []
        while True:
            response = table.scan(**scan_kwargs)
            events.extend(response.get("Items", []))
            if "LastEvaluatedKey" not in response:
                break
            scan_kwargs["ExclusiveStartKey"] = response["LastEvaluatedKey"]
        return {
            "statusCode": 200,
            "headers": HEADERS,
            "body": json.dumps({"events": events}),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": HEADERS,
            "body": json.dumps({"error": str(e)}),
        }
