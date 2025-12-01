import json
import os
import boto3


def instagram_id_exists(instagram_id: str, table):
    response = table.get_item(Key={"id": instagram_id}, ConsistentRead=True)
    return response.get("Item", None) is not None


def enqueue_instagram_id(instagram_id: str, table):
    print(f"Processing Instagram ID '{instagram_id}'")

    # put empty data for now
    table.put_item(Key={"id": instagram_id})

    # send message to queue
    sqs = boto3.client("sqs")
    queue_url = os.environ["INSTAGRAM_ID_QUEUE_URL"]
    sqs.send_message(
        QueueUrl=queue_url, MessageBody=json.dumps({"id": instagram_id})
    )


def handler(event, context):
    try:
        event_body = json.loads(event.get("body", "{}"))
        instagram_id = event_body.get("instagramId", "").strip()
        if instagram_id == "":
            raise Exception("Instagram ID is empty string")

        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ["DYNAMO_EVENTS_TABLE_NAME"]
        table = dynamodb.Table(table_name)

        id_exists = instagram_id_exists(instagram_id, table)
        if not id_exists:
            enqueue_instagram_id(instagram_id, table)

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "enqueued": not id_exists,
                }
            ),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "enqueued": False,
                    "error": str(e),
                }
            ),
        }
