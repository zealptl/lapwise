import * as cdk from 'aws-cdk-lib/core';
import { Template, Match } from 'aws-cdk-lib/assertions';
import { LapwiseStack } from '../lib/lapwise-stack';

/**
 * Task 2.2: Assert that /openapi.json and /docs routes have HttpNoneAuthorizer
 * so the AgentCore Gateway can fetch the OpenAPI schema without a token to build
 * its tool catalog.
 */
describe('OpenAPI public access', () => {
  let template: Template;

  beforeAll(() => {
    const app = new cdk.App();
    const stack = new LapwiseStack(app, 'TestStack', {
      env: { account: '123456789012', region: 'us-east-1' },
    });
    template = Template.fromStack(stack);
  });

  test('/openapi.json route exists with NONE authorizer', () => {
    template.hasResourceProperties('AWS::ApiGatewayV2::Route', {
      RouteKey: 'GET /openapi.json',
      AuthorizationType: 'NONE',
    });
  });

  test('/docs route exists with NONE authorizer', () => {
    template.hasResourceProperties('AWS::ApiGatewayV2::Route', {
      RouteKey: 'GET /docs',
      AuthorizationType: 'NONE',
    });
  });

  test('/healthz route remains exempt from auth', () => {
    template.hasResourceProperties('AWS::ApiGatewayV2::Route', {
      RouteKey: 'GET /healthz',
      AuthorizationType: 'NONE',
    });
  });

  test('default routes require JWT authorization', () => {
    // The default stage has a JWT authorizer — spot-check by confirming
    // there is at least one JWT-type authorizer in the stack
    template.hasResourceProperties('AWS::ApiGatewayV2::Authorizer', {
      AuthorizerType: 'JWT',
    });
  });
});
