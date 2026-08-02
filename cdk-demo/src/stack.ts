import * as cdk from 'aws-cdk-lib';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as path from 'path';
import { aws_bedrockagentcore as agentcore } from 'aws-cdk-lib';
import { Construct } from 'constructs';

export class TravelDisruptionStack extends cdk.Stack {
  public readonly harnessArn: cdk.CfnOutput;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ── DynamoDB: Passenger Profiles ──────────────────────────────────
    const passengerTable = new dynamodb.Table(this, 'PassengerTable', {
      tableName: 'TravelPassengerProfiles',
      partitionKey: { name: 'passenger_id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: cdk.RemovalPolicy.DESTROY,   // demo — destroy with stack
    });

    // ── Lambda: Flight Agent ──────────────────────────────────────────
    const flightAgentFn = new lambda.Function(this, 'FlightAgentFn', {
      functionName: 'travel-demo-flight-agent',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/flight-agent')),
      timeout: cdk.Duration.seconds(30),
      environment: {
        PASSENGER_TABLE: passengerTable.tableName,
      },
      description: 'Mock GDS flight rebooking tool for Travel Disruption demo',
    });
    passengerTable.grantReadData(flightAgentFn);

    // ── Lambda: Notify Agent ──────────────────────────────────────────
    const notifyAgentFn = new lambda.Function(this, 'NotifyAgentFn', {
      functionName: 'travel-demo-notify-agent',
      runtime: lambda.Runtime.PYTHON_3_12,
      handler: 'index.lambda_handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/notify-agent')),
      timeout: cdk.Duration.seconds(30),
      description: 'Mock traveler notification tool for Travel Disruption demo',
    });

    // ── IAM: Gateway Service Role ─────────────────────────────────────
    // The Gateway assumes this role to invoke Lambda functions.
    const gatewayRole = new iam.Role(this, 'GatewayServiceRole', {
      roleName: 'TravelGatewayServiceRole',
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      description: 'Service role for Travel Disruption AgentCore Gateway',
    });
    flightAgentFn.grantInvoke(gatewayRole);
    notifyAgentFn.grantInvoke(gatewayRole);

    // ── IAM: Harness Execution Role ───────────────────────────────────
    const executionRole = new iam.Role(this, 'HarnessExecutionRole', {
      roleName: 'TravelHarnessCdkRole',
      assumedBy: new iam.ServicePrincipal('bedrock-agentcore.amazonaws.com'),
      description: 'Execution role for Travel Disruption AgentCore Harness',
    });

    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'BedrockModelInvoke',
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock:InvokeModel',
        'bedrock:InvokeModelWithResponseStream',
        'bedrock:GetInferenceProfile',
        'bedrock:ListInferenceProfiles',
      ],
      resources: ['*'],
    }));

    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'AgentCoreMemoryAccess',
      effect: iam.Effect.ALLOW,
      actions: [
        'bedrock-agentcore:GetMemory',
        'bedrock-agentcore:CreateMemory',
        'bedrock-agentcore:UpdateMemory',
        'bedrock-agentcore:ListMemories',
        'bedrock-agentcore:PutMemoryRecord',
        'bedrock-agentcore:GetMemoryRecord',
        'bedrock-agentcore:ListMemoryRecords',
        'bedrock-agentcore:DeleteMemoryRecord',
        'bedrock-agentcore:ListEvents',
        'bedrock-agentcore:CreateEvent',
        'bedrock-agentcore:GetEvent',
        'bedrock-agentcore:DeleteEvent',
      ],
      resources: ['*'],
    }));

    // Allow harness to invoke the gateway
    executionRole.addToPolicy(new iam.PolicyStatement({
      sid: 'AgentCoreGatewayInvoke',
      effect: iam.Effect.ALLOW,
      actions: ['bedrock-agentcore:InvokeGateway'],
      resources: ['*'],
    }));

    // ── AgentCore Memory ──────────────────────────────────────────────
    const memory = new agentcore.CfnMemory(this, 'TravelMemory', {
      name: 'TravelPassengerMemory',
      eventExpiryDuration: 30,
      memoryExecutionRoleArn: executionRole.roleArn,
      memoryStrategies: [
        {
          semanticMemoryStrategy: {
            name: 'PassengerContextStrategy',
          },
        },
      ],
    });

    // ── AgentCore Gateway ─────────────────────────────────────────────
    // MCP protocol, AWS_IAM inbound auth.
    // The harness authenticates to the gateway using SigV4.
    const gateway = new agentcore.CfnGateway(this, 'TravelGateway', {
      name: 'TravelDisruptionGateway',
      description: 'Gateway exposing Flight and Notify tools for Travel Disruption agent',
      protocolType: 'MCP',
      authorizerType: 'AWS_IAM',
      roleArn: gatewayRole.roleArn,
    });

    // ── Tool schema: rebook_flight ────────────────────────────────────
    const rebookFlightSchema: agentcore.CfnGatewayTarget.ToolDefinitionProperty[] = [{
      name: 'rebook_flight',
      description: (
        'Find the next available flight matching the passenger\'s original route and cabin class, ' +
        'and confirm the rebooking. Use this when a flight has been cancelled or significantly delayed ' +
        'and a replacement flight must be confirmed. Returns full booking confirmation including ' +
        'flight number, departure time, seat, and confirmation code.'
      ),
      inputSchema: {
        type: 'object',
        properties: {
          passenger_id:    { type: 'string', description: 'Unique passenger identifier or name' },
          origin:          { type: 'string', description: 'IATA origin airport code, e.g. JFK' },
          destination:     { type: 'string', description: 'IATA destination airport code, e.g. LAX' },
          original_flight: { type: 'string', description: 'Cancelled or delayed flight number' },
          cabin_class:     { type: 'string', description: 'economy | business | first' },
          max_hours:       { type: 'integer', description: 'Max hours until next departure (default 8)' },
        },
        required: ['passenger_id', 'origin', 'destination', 'original_flight', 'cabin_class'],
      },
    }];

    // ── Gateway Target: Flight Agent ──────────────────────────────────
    const flightTarget = new agentcore.CfnGatewayTarget(this, 'FlightTarget', {
      name: 'FlightRebookingTarget',
      gatewayIdentifier: gateway.ref,
      // GATEWAY_IAM_ROLE: gateway uses its service role to invoke Lambda.
      // credentialProvider sub-object must NOT be set for Lambda targets.
      credentialProviderConfigurations: [{
        credentialProviderType: 'GATEWAY_IAM_ROLE',
      }],
      targetConfiguration: {
        mcp: {
          lambda: {
            lambdaArn: flightAgentFn.functionArn,
            toolSchema: { inlinePayload: rebookFlightSchema },
          },
        },
      },
    });
    flightTarget.addResourceDependency(gateway);

    // ── Tool schema: notify_traveler ──────────────────────────────────
    const notifyTravelerSchema: agentcore.CfnGatewayTarget.ToolDefinitionProperty[] = [{
      name: 'notify_traveler',
      description: (
        'Send a notification to the traveler about their rebooking and recovery details. ' +
        'Use after all rebooking and compensation steps are complete. ' +
        'Returns delivery confirmation with message ID and channels used.'
      ),
      inputSchema: {
        type: 'object',
        properties: {
          passenger_id:        { type: 'string', description: 'Passenger identifier' },
          channel:             { type: 'string', description: 'sms | email | push | all' },
          subject:             { type: 'string', description: 'Notification subject or title' },
          message:             { type: 'string', description: 'Full notification message body' },
          contact:             { type: 'string', description: 'Passenger phone or email' },
          new_flight:          { type: 'string', description: 'New flight number, e.g. AA457' },
          confirmation_number: { type: 'string', description: 'Booking confirmation code' },
        },
        required: ['passenger_id', 'channel', 'subject', 'message'],
      },
    }];

    // ── Gateway Target: Notify Agent ──────────────────────────────────
    const notifyTarget = new agentcore.CfnGatewayTarget(this, 'NotifyTarget', {
      name: 'TravelerNotificationTarget',
      gatewayIdentifier: gateway.ref,
      credentialProviderConfigurations: [{
        credentialProviderType: 'GATEWAY_IAM_ROLE',
      }],
      targetConfiguration: {
        mcp: {
          lambda: {
            lambdaArn: notifyAgentFn.functionArn,
            toolSchema: { inlinePayload: notifyTravelerSchema },
          },
        },
      },
    });
    notifyTarget.addResourceDependency(gateway);

    // ── System Prompt ─────────────────────────────────────────────────
    const systemPromptText = [
      'You are an autonomous travel disruption recovery agent.',
      'When a flight is cancelled or severely delayed, recover the affected passenger completely.',
      'For each passenger you must:',
      '1. Call rebook_flight to find and confirm a replacement flight.',
      '2. Call notify_traveler with the full rebooking details once confirmed.',
      '3. For overnight delays, note a hotel recommendation (hotel booking coming soon).',
      '4. Calculate compensation entitlement based on loyalty tier (Gold: 5000 miles or $150 voucher).',
      '5. Call escalate_to_agent for special cases: unaccompanied minors, medical needs, or groups > 8.',
      'Always call rebook_flight and notify_traveler — do not just describe what you would do.',
      'Think step by step. Be specific with flight numbers, times, and confirmation codes.',
    ].join(' ');

    // ── AgentCore Harness ─────────────────────────────────────────────
    const harness = new agentcore.CfnHarness(this, 'TravelHarness', {
      harnessName: 'travel_disruption_demo',
      executionRoleArn: executionRole.roleArn,

      model: {
        bedrockModelConfig: {
          modelId: 'us.anthropic.claude-sonnet-4-6',
        },
      },

      systemPrompt: [{ text: systemPromptText }],

      // Gateway tool — exposes rebook_flight + notify_traveler
      // Inline function — escalate_to_agent (human-in-the-loop)
      tools: [
        {
          type: 'agentcore_gateway',
          name: 'travel-gateway',
          config: {
            agentCoreGateway: {
              gatewayArn: agentcore.CfnGateway.arnForGateway(gateway),
              outboundAuth: { awsIam: {} },
            },
          },
        },
        {
          type: 'inline_function',
          name: 'escalate_to_agent',
          config: {
            inlineFunction: {
              description: [
                'Escalate to a human agent for passengers requiring special handling.',
                'MUST be called for: unaccompanied minors, medical assistance,',
                'groups over 8, or any out-of-policy situation.',
              ].join(' '),
              inputSchema: {
                type: 'object',
                properties: {
                  passenger_id: { type: 'string' },
                  reason:       { type: 'string' },
                  urgency:      { type: 'string', enum: ['low', 'medium', 'high'] },
                  details:      { type: 'string' },
                },
                required: ['passenger_id', 'reason', 'urgency'],
              },
            },
          },
        },
      ],

      // Scope to exactly the three tools.
      // Format: {CfnGatewayTarget.name}___{toolName}
      // The prefix is the gateway TARGET resource name, NOT the gateway name.
      allowedTools: [
        'FlightRebookingTarget___rebook_flight',
        'TravelerNotificationTarget___notify_traveler',
        'escalate_to_agent',
      ],

      memory: {
        agentCoreMemoryConfiguration: {
          arn: agentcore.CfnMemory.arnForMemory(memory),
        },
      },

      maxIterations: 15,
      timeoutSeconds: 120,

      tags: [
        { key: 'Project',     value: 'TravelDisruptionDemo' },
        { key: 'Environment', value: 'Demo' },
      ],
    });

    harness.addResourceDependency(memory);
    harness.addResourceDependency(gateway);
    harness.addResourceDependency(flightTarget);
    harness.addResourceDependency(notifyTarget);

    // ── Stack Outputs ─────────────────────────────────────────────────
    this.harnessArn = new cdk.CfnOutput(this, 'HarnessArn', {
      value: agentcore.CfnHarness.arnForHarness(harness),
      description: 'AgentCore Harness ARN — pass to demo.py --harness-arn',
      exportName: 'TravelDisruptionHarnessArn',
    });

    new cdk.CfnOutput(this, 'GatewayArn', {
      value: agentcore.CfnGateway.arnForGateway(gateway),
      description: 'AgentCore Gateway ARN',
      exportName: 'TravelDisruptionGatewayArn',
    });

    new cdk.CfnOutput(this, 'PassengerTableName', {
      value: passengerTable.tableName,
      description: 'DynamoDB Passenger Profiles table',
    });

    new cdk.CfnOutput(this, 'DemoCommand', {
      value: [
        'python3 ../demo.py',
        '--region', cdk.Stack.of(this).region,
        '--skip-create',
        '--harness-arn', agentcore.CfnHarness.arnForHarness(harness),
        '--no-cleanup',
      ].join(' '),
      description: 'Run the demo against the deployed stack',
    });
  }
}
