import json
import os
import boto3
import requests
import base64


def instagram_id_exists(instagram_id: str, table):
    response = table.get_item(Key={"id": instagram_id}, ConsistentRead=True)
    return response.get("Item", None) is not None


def fetch_and_save_instagram_preview(instagram_id: str, instagram_url: str, table):
    link_preview_api_key = os.environ["LINK_PREVIEW_API_KEY"]
    link_preview_api_url = os.environ["LINK_PREVIEW_API_URL"]
    response = requests.get(
        link_preview_api_url,
        headers={"X-Linkpreview-Api-Key": link_preview_api_key},
        params={"q": instagram_url},
    )
    preview_data = response.json()

    table.update_item(
        Key={"id": instagram_id},
        UpdateExpression="set preview_data = :p",
        ExpressionAttributeValues={":p": preview_data},
    )
    return preview_data


def has_food(preview_data: dict):
    return True


def generate_ai_data(context: str, image_bytes: bytes):
    client = boto3.Session().client("bedrock-runtime", region_name="us-east-1")
    MODEL_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"
    TEMPERATURE = 0
    MAX_TOKENS = 4096

    tool_name = "generate_event_data"

    schema = {
        "description": "Schema for summarizing an instagram event post",
        "type": "object",
        "properties": {
            "event_name": {
                "type": "string",
                "description": "name of the event.",
                "maxLength": 15,
            },
            "description": {
                "type": "string",
                "description": "A description summary that is only to 1-2 sentences. Only whats happening at the event. Leave out time, place and event name. Keep it simple and fun",
                "maxLength": 300,
            },
            "has_food_or_drinks": {
                "type": "boolean",
                "description": "Whether the post has food or drinks.",
            },
            "food_or_drinks": {
                "type": "string",
                "description": "Concisely list the food/drinks that are being served at the event.",
                "maxLength": 20,
            },
            "datetime": {
                "type": "string",
                "pattern": "\d{2}/\d{2}/\d{4} \d{1,2}:\d{2}",
                "description": "The date and time of the event. If the month is november or december, use the year 2025. Otherwise, use the year 2026.",
                "maxLength": 20,
            },
            "location": {
                "type": "string",
                "description": "The location of the event.",
                "maxLength": 20,
            },
        },
        "required": ["event_name", "description", "has_food_or_drinks", "food_or_drinks", "datetime", "location"],
    }
    input_data = context

    tool_list = [
        {
            "toolSpec": {
                "name": tool_name,
                "description": "Generate event data from the input.",
                "inputSchema": {"json": schema},
            }
        }
    ]

    messages = [
        {
            "role": "user",
            "content": [
                {"text": json.dumps(input_data)},
                {
                    "image": {
                        "format": "jpeg",
                        "source": {
                            "bytes": image_bytes
                        }
                    }
                },
            ],
        },
    ]
    response_converse = client.converse(
        modelId=MODEL_ID,
        messages=messages,
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": TEMPERATURE},
        toolConfig={
            "tools": tool_list,
            "toolChoice": {"tool": {"name": tool_name}},
        },
    )

    response_content = (
        response_converse.get("output", {})
        .get("message", {})
        .get("content", [{}])[0]
        .get("toolUse", {})
        .get("input", {})
    )

    return response_content


def generate_and_save_ai_data(instagram_id: str, instagram_url: str, preview_data: dict, table):
    image_url = preview_data.get("image", "")
    req = requests.get(image_url)
    image_bytes = req.content
    title = preview_data.get("title", "")
    description = preview_data.get("description", "")

    prompt = "You are an expert events summarizer."

    context = {
        "prompt": prompt,
        "title": title,
        "description": description,
    }

    ai_data = {**generate_ai_data(context, image_bytes), "instagram_url": instagram_url}
    table.update_item(
        Key={"id": instagram_id},
        UpdateExpression="set ai_data = :d",
        ExpressionAttributeValues={":d": ai_data},
    )
    
    return ai_data


# dequeue oldest instagram id from queue
def dequeue_instagram_id():
    sqs = boto3.client("sqs")
    queue_url = os.environ["INSTAGRAM_ID_QUEUE_URL"]

    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20
    )
    message = response.get("Messages", [{}])[0]
    data = json.loads(message.get("Body", "{}"))
    receipt_handle = message.get("ReceiptHandle", None)
    if receipt_handle:
        sqs.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)

    instagram_id = data.get("id", None)
    if instagram_id is None:
        raise Exception("Instagram ID is None in message body")

    return instagram_id


def handler(event, context):
    try:
        instagram_id = dequeue_instagram_id()
        instagram_url = f"https://www.instagram.com/p/{instagram_id}/"


        dynamodb = boto3.resource("dynamodb")
        table_name = os.environ["DYNAMO_EVENTS_TABLE_NAME"]
        table = dynamodb.Table(table_name)
        preview_data = fetch_and_save_instagram_preview(instagram_id, instagram_url, table)
        if has_food(preview_data):
            generate_and_save_ai_data(instagram_id, instagram_url, preview_data, table)
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
