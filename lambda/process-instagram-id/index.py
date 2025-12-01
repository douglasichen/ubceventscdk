from dataclasses import dataclass


@dataclass
class InstagramIdEvent:
    instagramId: str


def process_instagram_id(instagram_id: str):
    print(f"Processing Instagram ID: {instagram_id}")


def handler(event: InstagramIdEvent):
    instagram_id = event.instagramId
    already_processed = False

    if already_processed:
        return {
            "statusCode": 200,
            "body": {
                "alreadyProcessed": True,
                "processed": False,
            },
        }

    process_instagram_id(instagram_id)

    return {
        "statusCode": 200,
        "body": {
            "alreadyProcessed": False,
            "processed": True,
        },
    }
