import * as path from 'path';
import * as cdk from 'aws-cdk-lib/core';
import * as cognito from 'aws-cdk-lib/aws-cognito';
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

    // ── Cognito User Pool (task 4.3) ──────────────────────────────────────────
    const userPool = new cognito.UserPool(this, 'LapwiseUserPool', {
      signInAliases: { email: true },
      selfSignUpEnabled: false,
    });

    const userPoolClient = userPool.addClient('LapwiseAppClient', {
      authFlows: { userPassword: true },
    });

    // ── API Gateway access log group (task 4.8) ───────────────────────────────
    const apiLogGroup = new logs.LogGroup(this, 'ApiLogGroup', {
      retention: logs.RetentionDays.ONE_MONTH,
    });

    // API Gateway needs write access to the log group
    apiLogGroup.grantWrite(new iam.ServicePrincipal('apigateway.amazonaws.com'));

    // ── JWT authorizer backed by Cognito (task 4.5) ───────────────────────────
    const jwtAuthorizer = new HttpJwtAuthorizer(
      'CognitoAuthorizer',
      `https://cognito-idp.${this.region}.amazonaws.com/${userPool.userPoolId}`,
      { jwtAudience: [userPoolClient.userPoolClientId] },
    );

    // ── HTTP API — default authorizer covers all routes (tasks 4.4, 4.6) ─────
    const api = new apigwv2.HttpApi(this, 'LapwiseApi', {
      defaultIntegration: new HttpLambdaIntegration('LambdaIntegration', fn),
      defaultAuthorizer: jwtAuthorizer,
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
  }
}
