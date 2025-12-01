import json
import os
import boto3


def instagram_id_exists(instagram_id: str, table):
    response = table.get_item(Key={"id": instagram_id}, ConsistentRead=True)
    return response.get("Item", None) is not None

# dequeue oldest instagram id from queue
def dequeue_instagram_id():

    sqs = boto3.client("sqs")
    queue_url = os.environ["INSTAGRAM_ID_QUEUE_URL"]

    response = sqs.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1)

    print(json.dumps(response, indent=4))
    return 


def handler(event, context):
    try:
        dequeue_instagram_id()
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
