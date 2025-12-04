import * as cdk from "aws-cdk-lib";
import * as iam from "aws-cdk-lib/aws-iam";
import * as events from "aws-cdk-lib/aws-events";
import * as targets from "aws-cdk-lib/aws-events-targets";
import { Construct } from "constructs";
import * as sqs from "aws-cdk-lib/aws-sqs";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import * as apigateway from "aws-cdk-lib/aws-apigateway";

export class UbceventscdkStack extends cdk.Stack {
  private createSecureGetEventsLambda(dynamoEventsTable: dynamodb.Table) {// 1. The Backend (Lambda)
    const safeHandler = new lambda.Function(this, 'SafeHandler', {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset('lambda/get-events'),
      handler: 'index.handler',
    });

    // 2. The API (with CORS and Throttling)
    const api = new apigateway.RestApi(this, 'SafeApi', {
      restApiName: 'ThrottledPublicService',
      deployOptions: {
        stageName: 'prod',
        throttlingRateLimit: 2,
        throttlingBurstLimit: 2,
      },
      defaultCorsPreflightOptions: {
        // change to just freefoodatubc.ca in production
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
      },
    });

    const integration = new apigateway.LambdaIntegration(safeHandler);
    api.root.addMethod('GET', integration);
  }

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const dynamoEventsTable = new dynamodb.Table(this, "DyanmoEventsTable", {
      tableName: "dynamo-events-table",
      partitionKey: { name: "id", type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 25,
      writeCapacity: 25,
    });

    const instagramIdQueue = new sqs.Queue(this, "InstagramIdQueue", {
      queueName: "instagram-id-queue.fifo",
      fifo: true,
    });

    const enqueueInstagramIdLambda = new lambda.Function(
      this,
      "EnqueueInstagramIdLambda",
      {
        runtime: lambda.Runtime.PYTHON_3_10,
        code: lambda.Code.fromAsset("lambda/enqueue-instagram-id"),
        handler: "index.handler",
        environment: {
          DYNAMO_EVENTS_TABLE_NAME: dynamoEventsTable.tableName,
          INSTAGRAM_ID_QUEUE_NAME: instagramIdQueue.queueName,
          INSTAGRAM_ID_QUEUE_URL: instagramIdQueue.queueUrl,
        },
      }
    );

    const enqueueInstagramIdLambdaFunctionUrl =
      enqueueInstagramIdLambda.addFunctionUrl({
        authType: lambda.FunctionUrlAuthType.NONE,
      });

    dynamoEventsTable.grantReadWriteData(enqueueInstagramIdLambda);
    instagramIdQueue.grantSendMessages(enqueueInstagramIdLambda);

    const dequeueInstagramIdLambda = new lambda.Function(
      this,
      "DequeueInstagramIdLambda",
      {
        runtime: lambda.Runtime.PYTHON_3_10,
        code: lambda.Code.fromAsset("lambda/dequeue-instagram-id"),
        handler: "index.handler",
        environment: {
          DYNAMO_EVENTS_TABLE_NAME: dynamoEventsTable.tableName,
          INSTAGRAM_ID_QUEUE_URL: instagramIdQueue.queueUrl,
          LINK_PREVIEW_API_KEY: process.env.LINK_PREVIEW_API_KEY || "",
          LINK_PREVIEW_API_URL: process.env.LINK_PREVIEW_API_URL || "",
        },
        timeout: cdk.Duration.seconds(60),
      }
    );

    dequeueInstagramIdLambda.addToRolePolicy(
      new iam.PolicyStatement({
        effect: iam.Effect.ALLOW,
        actions: ["bedrock:InvokeModel"],
        resources: ["*"],
      })
    );

    dynamoEventsTable.grantReadWriteData(dequeueInstagramIdLambda);
    instagramIdQueue.grantConsumeMessages(dequeueInstagramIdLambda);

    const dequeueInstagramIdScheduleRule = new events.Rule(
      this,
      "DequeueInstagramIdScheduleRule",
      {
        schedule: events.Schedule.rate(cdk.Duration.minutes(2)),
      }
    );

    dequeueInstagramIdScheduleRule.addTarget(
      new targets.LambdaFunction(dequeueInstagramIdLambda)
    );

    this.createSecureGetEventsLambda(dynamoEventsTable);
  }
}
