#!/usr/bin/env bash
# deploy.sh — Deploy the Travel Disruption AgentCore Harness demo stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="TravelDisruptionStack"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Travel Disruption Agent — CDK Deploy                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  Region:  $REGION"
echo "  Stack:   $STACK_NAME"
echo ""

# Verify AWS credentials
echo "► Checking AWS credentials..."
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
echo "  Account: $ACCOUNT"
echo ""

# Bootstrap if needed (only required once per account/region)
echo "► Checking CDK bootstrap..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --region "$REGION" &>/dev/null; then
  echo "  Bootstrapping CDK in $REGION..."
  npx cdk bootstrap "aws://$ACCOUNT/$REGION" --region "$REGION"
else
  echo "  CDK already bootstrapped ✓"
fi
echo ""

# Install dependencies
echo "► Installing npm dependencies..."
npm install --silent
echo ""

# Synth to validate
echo "► Synthesising CloudFormation template..."
npx cdk synth --quiet
echo "  Synth OK ✓"
echo ""

# Deploy
echo "► Deploying stack (this takes ~2 min)..."
npx cdk deploy "$STACK_NAME" \
  --require-approval never \
  --outputs-file outputs.json \
  --region "$REGION"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Deploy complete!                                        ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Extract and display harness ARN
HARNESS_ARN=$(node -e "const o=require('./outputs.json'); console.log(o['$STACK_NAME']['HarnessArn'])")
echo "  Harness ARN: $HARNESS_ARN"
echo ""
echo "  Run the demo:"
echo ""
echo "    cd .."
echo "    .venv/bin/python demo.py \\"
echo "      --region $REGION \\"
echo "      --skip-create \\"
echo "      --harness-arn \"$HARNESS_ARN\" \\"
echo "      --no-cleanup"
echo ""
