#!/usr/bin/env bash
# destroy.sh — Tear down the Travel Disruption AgentCore Harness demo stack
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

REGION="${AWS_REGION:-us-east-1}"
STACK_NAME="TravelDisruptionStack"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Travel Disruption Agent — CDK Destroy                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "  This will permanently delete:"
echo "    • AgentCore Harness (travel_disruption_demo)"
echo "    • AgentCore Memory  (TravelPassengerMemory) + all stored sessions"
echo "    • IAM Role          (TravelHarnessCdkRole)"
echo ""
read -r -p "  Continue? [y/N] " confirm
if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
  echo "  Aborted."
  exit 0
fi
echo ""

echo "► Destroying stack $STACK_NAME in $REGION..."
npx cdk destroy "$STACK_NAME" --force --region "$REGION"

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║  Destroy complete — all demo resources removed.         ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
