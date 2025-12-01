import json
import os
import boto3
import requests
import base64


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


def has_food(preview_data: dict):
    return True


def generate_ai_data(context: str, base64_image: str):
    client = boto3.Session().client("bedrock-runtime", region_name="us-east-1")
    MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"
    TEMPERATURE = 0
    MAX_TOKENS = 4096

    schema = {
        "description": "Schema for summarizing an instagram event post",
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "Title of the event.",
                "maxLength": 25,
            },
            "description": {
                "type": "string",
                "description": "A description summary that is only to 1-2 sentences. Only whats happening at the event. Leave out time, place and event title. Keep it simple and fun",
                "maxLength": 300,
            },
        },
        "required": ["title", "description"],
    }
    instructions = "Extract event data from the input."
    input_data = context

    tool_list = [
        {
            "toolSpec": {
                "name": "analyze_customer_review",
                "description": "Analyze customer reviews.",
                "inputSchema": {"json": schema},
            }
        }
    ]

    print("previous base64_image", base64_image[:10])
    media_type = base64_image.split(",")[0].split(":")[1].split("/")[1]
    base64_image = base64_image.split(",")[1]

    print("media_type", media_type)
    print("base64_image", base64_image[:10])

    # handle edge case
    if media_type == "image/jpg":
        media_type = "image/jpeg"

    message = {
        "role": "user",
        "content": [
            {"type": "text", "text": instructions},
            {"type": "text", "text": json.dumps(input_data)},
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": media_type,
                    "data": base64_image,
                },
            },
        ],
    }
    response_converse = client.converse(
        modelId=MODEL_ID,
        messages=[message],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": TEMPERATURE},
        toolConfig={
            "tools": tool_list,
            "toolChoice": {"tool": {"name": "generate_event_data"}},
        },
    )

    print(response_converse)


def generate_and_save_ai_data(instagram_id: str, preview_data: dict):
    image_url = preview_data.get("image", "")
    base64_image = base64.b64encode(requests.get(image_url).content).decode("utf-8")

    post_url = preview_data.get("url", "")
    title = preview_data.get("title", "")
    description = preview_data.get("description", "")

    system_prompt = "You are an expert events summarizer."

    print(
        {
            system_prompt: system_prompt,
            title: title,
            description: description,
            base64_image: f"{base64_image[:10]}...",
            post_url: post_url,
        }
    )
    pass


# dequeue oldest instagram id from queue
def dequeue_instagram_id():
    sqs = boto3.client("sqs")
    queue_url = os.environ["INSTAGRAM_ID_QUEUE_URL"]

    response = sqs.receive_message(
        QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=20
    )
    message = response.get("Messages", [{}])[0]
    print(message)
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
        preview_data = fetch_and_save_instagram_preview(instagram_id)
        if has_food(preview_data):
            generate_and_save_ai_data(instagram_id, preview_data)
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
