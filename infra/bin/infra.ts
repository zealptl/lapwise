#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib/core';
import { LapwiseStack } from '../lib/lapwise-stack';

const app = new cdk.App();
new LapwiseStack(app, 'LapwiseStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION ?? 'us-east-1',
  },
});
