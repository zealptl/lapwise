import { execSync } from 'child_process';
import * as path from 'path';
import * as cdk from 'aws-cdk-lib/core';
import * as cognito from 'aws-cdk-lib/aws-cognito';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as ecr_assets from 'aws-cdk-lib/aws-ecr-assets';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as logs from 'aws-cdk-lib/aws-logs';
import { CfnStage } from 'aws-cdk-lib/aws-apigatewayv2';
import { Construct } from 'constructs';
import * as apigwv2 from '@aws-cdk/aws-apigatewayv2-alpha';
import { HttpLambdaIntegration } from '@aws-cdk/aws-apigatewayv2-integrations-alpha';
import { HttpJwtAuthorizer } from '@aws-cdk/aws-apigatewayv2-authorizers-alpha';

export class LapwiseStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── Lambda log group (task 4.2) ───────────────────────────────────────────
    const lambdaLogGroup = new logs.LogGroup(this, 'LambdaLogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // ── Lambda function (task 4.1) ────────────────────────────────────────────
    const fn = new lambda.DockerImageFunction(this, 'LapwiseFunction', {
      code: lambda.DockerImageCode.fromImageAsset(
        path.join(__dirname, '../../service'),
        { platform: ecr_assets.Platform.LINUX_AMD64 },
      ),
      memorySize: 512,
      timeout: cdk.Duration.seconds(30),
      logGroup: lambdaLogGroup,
    });

    // ── Cognito User Pool (task 4.3, self sign-up for chat UI: task 2.1) ─────
    const userPool = new cognito.UserPool(this, 'LapwiseUserPool', {
      signInAliases: { email: true },
      selfSignUpEnabled: true,
      autoVerify: { email: true },
    });

    const userPoolClient = userPool.addClient('LapwiseAppClient', {
      // userPassword kept for the CLI auth flow; userSrp added for the web UI
      authFlows: { userPassword: true, userSrp: true },
    });

    // ── API Gateway access log group (task 4.8) ───────────────────────────────
    const apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // API Gateway needs write access to the log group
    apiLogGroup.grantWrite(new iam.ServicePrincipal('apigateway.amazonaws.com'));

    // ── JWT authorizer backed by Cognito (task 4.5) ───────────────────────────
    // Support optional M2M client B (Gateway→Lapwise hop) via env var (task 3.5)
    const m2mClientBId = process.env.LAPWISE_M2M_CLIENT_B_ID;
    const jwtAudience = m2mClientBId
      ? [userPoolClient.userPoolClientId, m2mClientBId]
      : [userPoolClient.userPoolClientId];

    const jwtAuthorizer = new HttpJwtAuthorizer(
      'CognitoAuthorizer',
      `https://cognito-idp.${this.region}.amazonaws.com/${userPool.userPoolId}`,
      { jwtAudience },
    );

    // ── HTTP API — default authorizer covers all routes (tasks 4.4, 4.6) ─────
    // corsPreflight lets the browser-based chat UI call the API (task 2.5)
    const api = new apigwv2.HttpApi(this, 'LapwiseApi', {
      defaultIntegration: new HttpLambdaIntegration('LambdaIntegration', fn),
      defaultAuthorizer: jwtAuthorizer,
      corsPreflight: {
        allowOrigins: ['http://localhost:5173'],
        allowMethods: [
          apigwv2.CorsHttpMethod.GET,
          apigwv2.CorsHttpMethod.PUT,
          apigwv2.CorsHttpMethod.OPTIONS,
        ],
        allowHeaders: ['Authorization', 'Content-Type'],
      },
    });

    // ── Access logging on default stage (task 4.9) ────────────────────────────
    const cfnStage = api.defaultStage!.node.defaultChild as CfnStage;
    cfnStage.addPropertyOverride('AccessLogSettings', {
      DestinationArn: apiLogGroup.logGroupArn,
      Format: JSON.stringify({
        requestId: '$context.requestId',
        method: '$context.httpMethod',
        path: '$context.path',
        status: '$context.status',
        latency: '$context.responseLatency',
        ip: '$context.identity.sourceIp',
      }),
    });

    // ── /healthz exempt from auth (task 4.7) ─────────────────────────────────
    api.addRoutes({
      path: '/healthz',
      methods: [apigwv2.HttpMethod.GET],
      integration: new HttpLambdaIntegration('HealthzIntegration', fn),
      authorizer: new apigwv2.HttpNoneAuthorizer(),
    });

    // ── /openapi.json and /docs exempt from auth (tasks 2.1) ─────────────────
    // AgentCore Gateway fetches /openapi.json without a token to build its tool catalog
    api.addRoutes({
      path: '/openapi.json',
      methods: [apigwv2.HttpMethod.GET],
      integration: new HttpLambdaIntegration('OpenApiJsonIntegration', fn),
      authorizer: new apigwv2.HttpNoneAuthorizer(),
    });

    api.addRoutes({
      path: '/docs',
      methods: [apigwv2.HttpMethod.GET],
      integration: new HttpLambdaIntegration('DocsIntegration', fn),
      authorizer: new apigwv2.HttpNoneAuthorizer(),
    });

    // ── Conversations table (task 2.2) ────────────────────────────────────────
    const conversationTable = new dynamodb.Table(this, 'ConversationTable', {
      partitionKey: { name: 'actor_id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'session_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
    });

    // ── Conversations Lambda (task 2.3) ───────────────────────────────────────
    const agentCoreMemoryId = 'LapwiseF1Agent_LapwiseMemory-BpEoUO9hnK';
    const agentCoreMemoryArn = `arn:aws:bedrock-agentcore:${this.region}:${this.account}:memory/${agentCoreMemoryId}`;

    const conversationsAssetDir = path.join(__dirname, '../lambda/conversations');
    const conversationsFn = new lambda.Function(this, 'ConversationsFunction', {
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'handler.handler',
      // Bundle boto3 with the asset: the runtime's built-in boto3 may predate
      // the bedrock-agentcore data plane client.
      code: lambda.Code.fromAsset(conversationsAssetDir, {
        exclude: ['.venv', '__pycache__', '.pytest_cache', 'tests', 'uv.lock', '.gitignore'],
        bundling: {
          image: lambda.Runtime.PYTHON_3_12.bundlingImage,
          command: [
            'bash',
            '-c',
            'pip install --target /asset-output "boto3>=1.39.15" && cp handler.py /asset-output/',
          ],
          local: {
            tryBundle(outputDir: string): boolean {
              execSync(
                `uv pip install --quiet --python 3.12 --target "${outputDir}" "boto3>=1.39.15" && ` +
                  `cp "${path.join(conversationsAssetDir, 'handler.py')}" "${outputDir}/"`,
                { stdio: 'inherit', shell: '/bin/bash' },
              );
              return true;
            },
          },
        },
      }),
      memorySize: 256,
      timeout: cdk.Duration.seconds(30),
      environment: {
        CONVERSATION_TABLE: conversationTable.tableName,
        AGENTCORE_MEMORY_ID: agentCoreMemoryId,
      },
      logGroup: lambdaLogGroup,
    });

    // Scoped IAM: Query/PutItem on the table only, ListEvents on the memory only
    conversationsFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['dynamodb:Query', 'dynamodb:PutItem'],
        resources: [conversationTable.tableArn],
      }),
    );
    conversationsFn.addToRolePolicy(
      new iam.PolicyStatement({
        actions: ['bedrock-agentcore:ListEvents'],
        resources: [agentCoreMemoryArn],
      }),
    );

    // ── Conversations routes — default JWT authorizer applies (task 2.4) ─────
    const conversationsIntegration = new HttpLambdaIntegration(
      'ConversationsIntegration',
      conversationsFn,
    );
    api.addRoutes({
      path: '/v1/conversations',
      methods: [apigwv2.HttpMethod.GET],
      integration: conversationsIntegration,
    });
    api.addRoutes({
      path: '/v1/conversations/{sessionId}',
      methods: [apigwv2.HttpMethod.PUT],
      integration: conversationsIntegration,
    });
    api.addRoutes({
      path: '/v1/conversations/{sessionId}/messages',
      methods: [apigwv2.HttpMethod.GET],
      integration: conversationsIntegration,
    });

    // CORS preflight must bypass the JWT authorizer: the $default route catches
    // OPTIONS requests and would 401 them before API Gateway's automatic CORS
    // response. AWS-documented fix: an unauthorized OPTIONS /{proxy+} route,
    // which has higher priority than $default.
    api.addRoutes({
      path: '/{proxy+}',
      methods: [apigwv2.HttpMethod.OPTIONS],
      integration: conversationsIntegration,
      authorizer: new apigwv2.HttpNoneAuthorizer(),
    });

    // ── Stack outputs (task 4.10) ─────────────────────────────────────────────
    new cdk.CfnOutput(this, 'ApiUrl', {
      value: api.apiEndpoint,
      description: 'HTTP API Gateway endpoint URL',
    });
    new cdk.CfnOutput(this, 'UserPoolId', {
      value: userPool.userPoolId,
      description: 'Cognito User Pool ID',
    });
    new cdk.CfnOutput(this, 'AppClientId', {
      value: userPoolClient.userPoolClientId,
      description: 'Cognito App Client ID',
    });
    new cdk.CfnOutput(this, 'ConversationTableName', {
      value: conversationTable.tableName,
      description: 'DynamoDB conversations table name',
    });
  }
}
