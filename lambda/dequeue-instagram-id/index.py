import json
import os
import boto3
import requests
import base64
import anthropic
from typesafe_sdk import Choice, Noul, TypeSafeClient


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


# Jev classifies; the extraction model only runs on posts that pass FOOD_GATE.
# Thresholds from a 60-post hand-judged eval: >=0.9 caught 7/8 food events with ~3 false alarms.
FOOD_GATE = 0.45
FOOD_SHOW = 0.9

JEV_QUESTIONS = {
    "food_event": Noul(
        instructions="Will attendees of an event in this post be given or served food or drinks "
        "(e.g. pizza, snacks, coffee, bubble tea, refreshments)? Drinks alone count: an event offering "
        "only coffee, tea, hot chocolate or 'a hot beverage' is a yes. Restaurant/café ads, food for sale "
        "with no event, and posts that only mention food in passing do not count.",
    ),
    "drinks_event": Noul(
        instructions="Will attendees of an event in this post be given a drink, such as coffee, tea, "
        "hot chocolate or 'a hot beverage' (even if they bring their own mug)? Drinks for sale do not count.",
    ),
    "free": Choice(
        instructions="Is the food/drink (and entry) free for attendees?",
        criteria={
            "yes": "Explicitly free, or clearly provided at no cost",
            "no": "Costs money: tickets, paid entry, or food for sale",
            "unsure": "Not stated",
        },
    ),
}


def classify_with_jev(title: str, description: str, image_bytes: bytes):
    # ponytail: Instagram previews are ~1080px, inside Jev's 280-1568px window, so no resize.
    with TypeSafeClient() as client:
        res = client.system_one(
            state={"instagram_title": title, "caption": description, "post_image": "img-1"},
            questions=JEV_QUESTIONS,
            extra_body={"assets": {"img-1": {"type": "image", "format": "jpg",
                                             "data_base64": base64.b64encode(image_bytes).decode()}}},
            extra_headers={"TypeSafe-Danger-Zone-Images": "true"},
            timeout=30,
        )
    a = res.answers
    return {
        "food": max(float(a["food_event"].noul), float(a["drinks_event"].noul)),
        "free": a["free"].choice,
    }


def generate_ai_data(context: str, image_bytes: bytes):
    client = anthropic.Anthropic()
    MODEL_ID = "claude-haiku-5-5"
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
            "food_or_drinks": {
                "type": "string",
                "description": "Concisely list the food/drinks that are being served at the event.",
                "maxLength": 15,
            },
            "datetime": {
                "type": ["string", "null"],
                "pattern": r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$",
                "description": "The date and time of the event. Use the year 2026. Or null if the date is not present.",
                "maxLength": 20,
            },
            "location": {
                "type": "string",
                "description": "The location of the event.",
                "maxLength": 20,
            },
        },
        "required": ["event_name", "description", "food_or_drinks", "datetime", "location"],
    }
    response = client.messages.create(
        model=MODEL_ID,
        max_tokens=MAX_TOKENS,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": json.dumps(context)},
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": base64.b64encode(image_bytes).decode(),
                        },
                    },
                ],
            }
        ],
        tools=[{"name": tool_name, "description": "Generate event data from the input.", "input_schema": schema}],
        tool_choice={"type": "tool", "name": tool_name},
    )

    return next((b.input for b in response.content if b.type == "tool_use"), {})


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

    jev = classify_with_jev(title, description, image_bytes)
    table.update_item(
        Key={"id": instagram_id},
        UpdateExpression="set jev = :j",
        ExpressionAttributeValues={":j": {"food": str(jev["food"]), "free": jev["free"]}},
    )
    if jev["food"] < FOOD_GATE:
        return None

    ai_data = {
        **generate_ai_data(context, image_bytes),
        # The frontend filters on these two, so they keep their old names.
        "has_food_or_drinks": jev["food"] >= FOOD_SHOW,
        "free": jev["free"],
        "instagram_url": instagram_url,
    }
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
        print(f"dequeue failed: {e!r}")
        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "dequeued": False,
                    "error": str(e),
                }
            ),
        }
