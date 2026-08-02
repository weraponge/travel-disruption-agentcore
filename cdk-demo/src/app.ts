#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { TravelDisruptionStack } from './stack';

const app = new cdk.App();

new TravelDisruptionStack(app, 'TravelDisruptionStack', {
  env: {
    // Uses current AWS CLI credentials region, or override with CDK_DEFAULT_REGION
    account: process.env.CDK_DEFAULT_ACCOUNT || process.env.AWS_ACCOUNT_ID,
    region:  process.env.CDK_DEFAULT_REGION  || process.env.AWS_REGION || 'us-east-1',
  },
  description: 'Travel Disruption Agent — Amazon Bedrock AgentCore Harness Demo',
  tags: {
    Project: 'TravelDisruptionDemo',
  },
});

app.synth();
