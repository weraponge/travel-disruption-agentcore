# Travel Disruption Agent — Amazon Bedrock AgentCore Harness

An autonomous travel disruption recovery agent built on [Amazon Bedrock AgentCore Harness](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html). When a flight is cancelled, the agent recovers affected passengers in parallel — rebooking flights, sending notifications, and escalating edge cases to human agents — without writing any orchestration code.

## What this demonstrates

| AgentCore Harness feature | How it's used |
|---|---|
| Configuration-only agent | Entire agent defined via `create_harness` API — no orchestration code |
| AgentCore Gateway | Flight and Notify tools exposed as Lambda-backed MCP tools |
| AgentCore Memory | Passenger context persists across sessions |
| Inline function (human-in-loop) | Unaccompanied minor escalation pauses agent, routes to human |
| Per-invocation model switching | Claude Haiku for tool demos, Sonnet for escalation |
| Isolated microVM per session | Each passenger recovery runs in its own sandboxed environment |

## Architecture

```
Disrupted Traveler → Airline/GDS System
                         ↓
                   EventBridge → SQS
                         ↓
              ┌─ AgentCore Harness ──────────────────┐
              │  Orchestrator (Claude Sonnet 4.6)     │
              │  AgentCore Memory                     │
              │  ┌──────────────┬─────────────────┐  │
              │  │ Flight Agent │  Notify Agent   │  │
              │  │  (Lambda)    │   (Lambda)      │  │
              │  └──────┬───────┴────────┬────────┘  │
              └─────────┼────────────────┼───────────┘
                        ↓                ↓
               AgentCore Gateway (MCP, AWS_IAM)
                        ↓
               DynamoDB  SNS  Secrets Manager
```

> **Demo scope (Path B):** This repo deploys Flight Agent and Notify Agent Lambdas. Hotel Agent, Compensation Agent, EventBridge, SQS, and SNS follow the identical CDK pattern and can be added without changing the harness configuration.

## Prerequisites

- AWS CLI 2.x configured with credentials
- Node.js 20+
- Python 3.10+
- Access to `us.anthropic.claude-sonnet-4-6` in Amazon Bedrock (us-east-1)

## Deploy

```bash
cd cdk-demo

# First time only — bootstrap CDK in your account
npx cdk bootstrap

# Deploy all resources (~2 min)
./deploy.sh
```

At the end, `deploy.sh` prints the harness ARN and the exact `demo.py` command.

## Run the demo

```bash
# Install boto3
python3 -m venv .venv && .venv/bin/pip install boto3

# Run (harness ARN is read from cdk-demo/outputs.json automatically)
.venv/bin/python demo.py \
  --region us-east-1 \
  --skip-create \
  --harness-arn "<YOUR_HARNESS_ARN>" \
  --no-cleanup
```

### Demo scenarios

**Demo 1 — Standard recovery**
Cancels flight AA123, agent calls `rebook_flight` and `notify_traveler` tools via Gateway.

**Demo 2 — Memory**
Follow-up question on the same `runtimeSessionId` — agent answers from AgentCore Memory with no context re-sent.

**Demo 3 — Human-in-the-loop escalation**
Unaccompanied minor (Emma, age 9) triggers `escalate_to_agent` inline function, script intercepts and sends human decision back.

## Destroy

```bash
cd cdk-demo
./destroy.sh
```

Deletes all provisioned resources. Memory conversation history is also deleted.

## Project structure

```
.
├── demo.py                              # End-to-end demo script
├── travel-disruption-agentcore.yaml     # Architecture diagram source (awsdac)
├── blog-travel-disruption-agentcore.md  # Blog post (Markdown)
├── blog-travel-disruption-agentcore.html # Blog post (AWS-style HTML)
└── cdk-demo/
    ├── deploy.sh                        # One-command deploy
    ├── destroy.sh                       # One-command teardown
    ├── src/
    │   ├── app.ts                       # CDK entry point
    │   └── stack.ts                     # All resources defined here
    └── lambda/
        ├── flight-agent/index.py        # Mock GDS rebooking Lambda
        └── notify-agent/index.py        # Mock notification Lambda
```

## Resources deployed

| Type | Name |
|---|---|
| `AWS::BedrockAgentCore::Harness` | `travel_disruption_demo` |
| `AWS::BedrockAgentCore::Gateway` | `TravelDisruptionGateway` |
| `AWS::BedrockAgentCore::GatewayTarget` | `FlightRebookingTarget`, `TravelerNotificationTarget` |
| `AWS::BedrockAgentCore::Memory` | `TravelPassengerMemory` |
| `AWS::Lambda::Function` | `travel-demo-flight-agent`, `travel-demo-notify-agent` |
| `AWS::DynamoDB::Table` | `TravelPassengerProfiles` |
| `AWS::IAM::Role` | `TravelHarnessCdkRole`, `TravelGatewayServiceRole` |

## Related

- [AgentCore Harness documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html)
- [AgentCore Gateway documentation](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html)
- [Build a serverless image editing agent with AgentCore Harness](https://aws.amazon.com/blogs/machine-learning/build-a-serverless-image-editing-agent-with-amazon-bedrock-agentcore-harness/) — reference blog post
