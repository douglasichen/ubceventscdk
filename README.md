# UBC Events CDK

An AWS CDK (Cloud Development Kit) project that automatically processes Instagram posts (given only their ids) to extract and serve event information, with a focus on free food events at UBC (but can be customized for other use cases).

## Overview

This system scrapes Instagram posts (primarily from @theubcssa), processes them using AI to extract structured event data, and serves the information via a public REST API. The architecture is designed to handle Instagram post IDs asynchronously, using a queue-based processing system with AI-powered event extraction.

## Architecture

### Components

#### 1. **DynamoDB Table** (`dynamo-events-table`)
- **Purpose**: Stores processed event data
- **Partition Key**: `id` (Instagram post ID)
- **Schema**:
  - `id`: Instagram post ID (string)
  - `preview_data`: Link preview metadata (title, description, image URL)
  - `ai_data`: Structured event data extracted by AI, including:
    - `event_name`: Name of the event
    - `description`: 1-2 sentence summary
    - `has_food_or_drinks`: Boolean flag
    - `food_or_drinks`: List of food/drinks served
    - `datetime`: Event date/time (ISO format)
    - `location`: Event location
    - `free`: Whether the event is free (yes/no/unsure)
    - `instagram_url`: Link to the original Instagram post
- **Capacity**: Provisioned with 25 read/write capacity units

#### 2. **SQS FIFO Queue** (`instagram-id-queue.fifo`)
- **Purpose**: Queues Instagram post IDs to throttle processing of posts (limited by free instagram preview API)
- **Type**: FIFO (First-In-First-Out) to ensure ordered processing
- **Integration**: Receives messages from `enqueue-instagram-id` Lambda, consumed by `dequeue-instagram-id` Lambda

#### 3. **Lambda Functions**

##### `enqueue-instagram-id`
- **Runtime**: Python 3.10
- **Trigger**: Function URL (public, no authentication)
- **Purpose**: Receives Instagram post IDs and enqueues them for processing
- **Workflow**:
  1. Receives POST request with `instagramId` in body
  2. Checks if Instagram ID already exists in DynamoDB
  3. If new, creates a placeholder record in DynamoDB
  4. Sends message to SQS FIFO queue
- **Returns**: JSON object with `enqueued` field (true if new, false if already exists)
- **Permissions**: Read/Write access to DynamoDB, Send messages to SQS

##### `dequeue-instagram-id`
- **Runtime**: Python 3.10
- **Trigger**: EventBridge rule (every 2 minutes)
- **Timeout**: 60 seconds
- **Purpose**: Processes queued Instagram posts to extract event information
- **Workflow**:
  1. Dequeues one message from SQS FIFO queue
  2. Fetches link preview data using Link Preview API (title, description, image)
  3. Saves preview data to DynamoDB
  4. If food-related, uses AWS Bedrock (Claude Haiku) to extract structured event data:
     - Analyzes image and text context
     - Extracts event name, description, datetime, location, food info
     - Saves structured data to DynamoDB
- **Dependencies**: 
  - [Link Preview API](https://www.linkpreview.net/) (requires `LINK_PREVIEW_API_KEY` and `LINK_PREVIEW_API_URL` environment variables)
  - AWS Bedrock (Claude 4.5 Haiku model)
- **Permissions**: Read/Write access to DynamoDB, Consume messages from SQS, Invoke Bedrock models

##### `get-events`
- **Runtime**: Python 3.10
- **Trigger**: API Gateway REST API
- **Timeout**: 10 seconds
- **Purpose**: Public API endpoint to query events
- **Workflow**:
  1. Queries DynamoDB for events within date range (today to 2 weeks in future)
  2. Filters by `ai_data.datetime` field
  3. Returns JSON array of events
- **API Endpoint**: `GET /` (root path)
- **CORS**: Enabled for all origins (configure for production)
- **Throttling**: 10 requests/second, burst limit of 10 (ensures users can't spam the endpoint)
- **Permissions**: Read access to DynamoDB

#### 4. **API Gateway**
- **Type**: REST API
- **Stage**: `prod`
- **Features**:
  - CORS enabled
  - Rate limiting (10 req/s, burst 10)
  - Integrated with `get-events` Lambda

#### 5. **EventBridge Rule**
- **Schedule**: Every 2 minutes (Link Preview API free tier technically has a limit of 60 requests per hour and this can be increased to every minute)
- **Target**: `dequeue-instagram-id` Lambda
- **Purpose**: Triggers automatic processing of queued Instagram posts

### Data Flow

```
1. External System
   ↓ (POST Instagram ID)
   enqueue-instagram-id Lambda (Function URL)
   ↓ (if new)
   DynamoDB (create placeholder) + SQS FIFO Queue

2. EventBridge (every 2 minutes)
   ↓ (trigger)
   dequeue-instagram-id Lambda
   ↓ (dequeue from SQS)
   Link Preview API → Preview Data
   ↓ (if food-related)
   AWS Bedrock (Claude Haiku) → Structured Event Data
   ↓ (save)
   DynamoDB (update with preview_data and ai_data)

3. Public Client
   ↓ (GET request)
   API Gateway → get-events Lambda
   ↓ (query)
   DynamoDB (filter by date range)
   ↓ (return)
   JSON response with events
```

## Prerequisites

- Node.js (v22)
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Python 3.10 (for Lambda functions)

## Setup

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Configure environment variables**:
   Create a `.env` file or set environment variables:
   ```bash
   ACCOUNT_ID=your-aws-account-id
   REGION=your-aws-region
   AWS_ACCESS_KEY=your-aws-access-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret-access-key
   LINK_PREVIEW_API_KEY=your-api-key
   LINK_PREVIEW_API_URL=your-link-preview-api-url
   ```

3. **Deploy**:
   Deployment is automatically run on push to main; is configured with GitHub Actions [here](.github/workflows/deploy.yml) file

## Usage

### Enqueue an Instagram Post

Send a POST request to the `enqueue-instagram-id` Function URL:

```bash
curl -X POST https://<function-url> \
  -H "Content-Type: application/json" \
  -d '{"instagramId": "ABC123XYZ"}'
```

The Instagram ID should be the post ID from the Instagram URL (e.g., from `https://www.instagram.com/p/ABC123XYZ/`, the ID is `ABC123XYZ`).

### Query Events

Query events via the API Gateway endpoint:

```bash
curl https://<api-gateway-url>/prod
```

The API returns events from today up to 2 weeks in the future, filtered by the `ai_data.datetime` field.
