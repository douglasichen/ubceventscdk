import json
import os
import boto3
import requests


def instagram_id_exists(instagram_id: str, table):
    response = table.get_item(Key={"id": instagram_id}, ConsistentRead=True)
    return response.get("Item", None) is not None


def fetch_and_save_instagram_preview(instagram_id: str):
    url = f"https://www.instagram.com/p/{instagram_id}/"
    link_preview_api_key = os.environ["LINK_PREVIEW_API_KEY"]
    link_preview_api_url = os.environ["LINK_PREVIEW_API_URL"]
    response = requests.get(
        link_preview_api_url,
        headers={"X-Linkpreview-Api-Key": link_preview_api_key},
        params={"q": url},
    )
    preview_data = response.json()

    dynamodb = boto3.resource("dynamodb")
    table_name = os.environ["DYNAMO_EVENTS_TABLE_NAME"]
    table = dynamodb.Table(table_name)
    table.update_item(
        Key={"id": instagram_id},
        UpdateExpression="set preview_data = :p",
        ExpressionAttributeValues={":p": preview_data},
    )
    return preview_data


def generate_and_save_ai_data(preview_data: dict):
    pass

# dequeue oldest instagram id from queue
def dequeue_instagram_id():
    sqs = boto3.client("sqs")
    queue_url = os.environ["INSTAGRAM_ID_QUEUE_URL"]

    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20)
    message = response.get("Messages", [{}])[0]
    print(message)
    data = json.loads(message.get("Body", "{}"))
    receipt_handle = message.get("ReceiptHandle", None)
    if receipt_handle:
        sqs.delete_message(
            QueueUrl=queue_url,
            ReceiptHandle=receipt_handle
        )

    instagram_id = data.get("id", None)
    if instagram_id is None:
        raise Exception("Instagram ID is None in message body")

    return instagram_id


def handler(event, context):
    try:
        instagram_id = dequeue_instagram_id()
        preview_data = fetch_and_save_instagram_preview(instagram_id)
        ai_data = generate_and_save_ai_data(preview_data)
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "dequeued": True,
                }
            ),
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "dequeued": False,
                    "error": str(e),
                }
            ),
        }
