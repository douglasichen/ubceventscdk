import * as cdk from "aws-cdk-lib";
import { Construct } from "constructs";
import * as s3 from "aws-cdk-lib/aws-s3";
import * as lambda from "aws-cdk-lib/aws-lambda";

export class UbceventscdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    const eventsBucket = new s3.Bucket(this, "UbcEventsBucket", {
      bucketName: "ubc-events-bucket",
    });

    const instagramIdsBucket = new s3.Bucket(this, "InstagramIdsBucket", {
      bucketName: "instagram-ids-bucket",
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
