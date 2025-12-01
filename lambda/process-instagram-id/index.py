
import json
def process_instagram_id(instagram_id: str):
    print(f"Processing Instagram ID '{instagram_id}'")


def handler(event, context):

    instagram_id = event["instagramId"]
    already_processed = False

    if already_processed:
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({
                "alreadyProcessed": True,
                "processed": False,
            }),
        }

    try:
        process_instagram_id(instagram_id)
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({
                "alreadyProcessed": False,
                "processed": True,
            }),
        }
    except Exception as e:
        print(f"Error processing Instagram ID '{instagram_id}':", e)
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
            },
            "body": json.dumps({
                "alreadyProcessed": False,
                "processed": False,
            }),
        }