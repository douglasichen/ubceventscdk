import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";
import * as dynamodb from "aws-cdk-lib/aws-dynamodb";
import { LayerVersion } from "aws-cdk-lib/aws-lambda";

export class UbceventscdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const eventsBucket = new s3.Bucket(this, "UbcEventsBucket", {
      bucketName: "ubc-events-bucket",
    });

    // const processInstagramIdsLambda = new lambda.Function(this, "ProcessInstagramIdsLambda", {
    //   runtime: lambda.Runtime.NODEJS_22_X,
    //   code: lambda.Code.fromAsset("lambda/process-instagram-ids"),
    //   handler: "index.handler",
    // });


    // const fetchInstagramIdsLambda = new lambda.Function(this, "FetchInstagramIdsLambda", {
    //   runtime: lambda.Runtime.PYTHON_3_9,
    //   code: lambda.Code.fromAsset("lambda/fetch-instagram-ids"),
    //   handler: "index.handler",
    // });

    

    // const puppeteerLambda = new lambda.Function(this, "PuppeteerLambda", {
    //   runtime: lambda.Runtime.NODEJS_18_X,
    //   code: lambda.Code.fromAsset("lambda/pup"),
    //   handler: "index.handler",
    //   layers: [LayerVersion.fromLayerVersionArn(this, 'chromium-lambda-layer',
    //     'arn:aws:lambda:us-east-1:764866452798:layer:chrome-aws-lambda:50'
    //   )],
    //   memorySize: 1600,
    //   timeout: cdk.Duration.seconds(30),
    // });


    const dyanmoEventsTable = new dynamodb.Table(this, 'DyanmoEventsTable', {
      tableName: 'dynamo-events-table',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PROVISIONED,
      readCapacity: 25,
      writeCapacity: 25,
    });

    const processInstagramIdLambda = new lambda.Function(this, "ProcessInstagramIdLambda", {
      runtime: lambda.Runtime.PYTHON_3_10,
      code: lambda.Code.fromAsset("lambda/process-instagram-id"),
      handler: "index.handler",
      environment: {
        DYNAMO_EVENTS_TABLE_NAME: dyanmoEventsTable.tableName,
      }
    });

    dyanmoEventsTable.grantReadWriteData(processInstagramIdLambda);

    const processInstagramIdLambdaFunctionUrl = processInstagramIdLambda.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE,
    });

    // const instagramIdsBucket = new s3.Bucket(this, "InstagramIdsBucket", {
    //   bucketName: "instagram-ids",
    // });

    // const processInstagramIdsLambda = new lambda.Function(
    //   this,
    //   "ProcessInstagramIdsLambda",
    //   {
    //     runtime: lambda.Runtime.NODEJS_22_X,
    //     code: lambda.Code.fromAsset("lambda/process-instagram-ids"),
    //     handler: "index.handler",
    //   }
    // );
  }
}
