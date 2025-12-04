import json
import os
import boto3
from datetime import datetime, timedelta

HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
}


def handler(event, context):
    try:
        now = datetime.now()
        future = now + timedelta(weeks=2)
        start_date = now.strftime("%Y-%m-%dT%H:%M:%S")
        end_date = future.strftime("%Y-%m-%dT%H:%M:%S")

        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ["DYNAMO_EVENTS_TABLE_NAME"]
        table = dynamodb.Table(table_name)

        response = table.scan(
            FilterExpression="ai_data.#dt BETWEEN :start AND :end",
            ExpressionAttributeNames={"#dt": "datetime"},
            ExpressionAttributeValues={":start": start_date, ":end": end_date},
        )

        events = response.get("Items", [])
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
