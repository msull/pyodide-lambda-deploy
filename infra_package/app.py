#!/usr/bin/env python3

import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_lambda,
    aws_dynamodb,
)
from constructs import Construct


class BasicAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Define multiple API keys
        # Define the DynamoDB table
        table = aws_dynamodb.Table(
            self,
            "simplesingletable-standard",
            partition_key=aws_dynamodb.Attribute(
                name="pk", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="sk", type=aws_dynamodb.AttributeType.STRING
            ),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            # Optional: allows the table to be deleted when the stack is destroyed
        )

        # Define the Lambda function
        lambda_function = aws_lambda.Function(
            self,
            "ApiHandlerFunction",
            runtime=aws_lambda.Runtime.PYTHON_3_10,
            handler="app.handler",
            code=aws_lambda.Code.from_asset(
                "../lambda",
                bundling={
                    "image": aws_lambda.Runtime.PYTHON_3_10.bundling_image,
                    "platform": "linux/arm64",
                    "command": [
                        "bash",
                        "-c",
                        """
                        pip install -r requirements.txt -t /asset-output &&
                        cp -au . /asset-output
                        """,
                    ],
                },
            ),
            timeout=cdk.Duration.seconds(45),
            environment={"DYNAMODB_TABLE": table.table_name},
        )

        # Add Global Secondary Indexes

        # GSI: gsitype
        table.add_global_secondary_index(
            index_name="gsitype",
            partition_key=aws_dynamodb.Attribute(
                name="gsitype", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="gsitypesk", type=aws_dynamodb.AttributeType.STRING
            ),
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        # GSI: gsi1
        table.add_global_secondary_index(
            index_name="gsi1",
            partition_key=aws_dynamodb.Attribute(
                name="gsi1pk", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="pk", type=aws_dynamodb.AttributeType.STRING
            ),
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        # GSI: gsi2
        table.add_global_secondary_index(
            index_name="gsi2",
            partition_key=aws_dynamodb.Attribute(
                name="gsi2pk", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="pk", type=aws_dynamodb.AttributeType.STRING
            ),
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        # GSI: gsi3
        table.add_global_secondary_index(
            index_name="gsi3",
            partition_key=aws_dynamodb.Attribute(
                name="gsi3pk", type=aws_dynamodb.AttributeType.STRING
            ),
            sort_key=aws_dynamodb.Attribute(
                name="gsi3sk", type=aws_dynamodb.AttributeType.STRING
            ),
            projection_type=aws_dynamodb.ProjectionType.ALL,
        )

        # Grant full CRUD permissions to the Lambda function
        table.grant_full_access(lambda_function)

        # Add the Function URL
        function_url = lambda_function.add_function_url(
            auth_type=aws_lambda.FunctionUrlAuthType.NONE,  # We're handling auth in code
            cors=aws_lambda.FunctionUrlCorsOptions(
                allowed_origins=["*"],
                allowed_methods=[aws_lambda.HttpMethod.ALL],
                allowed_headers=["*"],
            ),
        )

        # Output the Function URL
        cdk.CfnOutput(self, "FunctionUrl", value=function_url.url)
        cdk.CfnOutput(self, "TableName", value=table.table_name)


app = cdk.App()
BasicAppStack(app, "PyodideLambdaDeploy")
app.synth()
