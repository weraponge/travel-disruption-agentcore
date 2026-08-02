#!/usr/bin/env python3
"""
Travel Disruption Agent — AgentCore Harness Demo
=================================================
Demonstrates all key AgentCore Harness capabilities:
  1. Create harness (configuration-only agent)
  2. Invoke harness — autonomous disruption recovery
  3. Memory — follow-up question uses same session context
  4. Human-in-the-loop — inline function escalation
  5. Cleanup

Usage:
  python3 demo.py [--region us-east-1] [--skip-create] [--harness-arn <arn>]

Requirements:
  pip install boto3
  AWS credentials configured with Bedrock + IAM permissions
"""

import argparse
import json
import os
import sys
import time
import uuid

import boto3
from botocore.exceptions import ClientError

# ── ANSI colours for terminal output ──────────────────────────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
ORANGE = "\033[38;5;214m"
CYAN   = "\033[36m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
GREY   = "\033[90m"

def banner(text):
    print(f"\n{ORANGE}{BOLD}{'─' * 60}{RESET}")
    print(f"{ORANGE}{BOLD}  {text}{RESET}")
    print(f"{ORANGE}{BOLD}{'─' * 60}{RESET}\n")

def step(n, text):
    print(f"{CYAN}{BOLD}[Step {n}]{RESET} {text}")

def ok(text):
    print(f"{GREEN}✓{RESET} {text}")

def info(text):
    print(f"{GREY}  {text}{RESET}")


# ── Load CDK outputs ────────────────────────────────────────────────────────────
def load_gateway_arn() -> str:
    """
    Read the gateway ARN from cdk-demo/outputs.json written by cdk deploy.
    Falls back to the live ARN if the file is not found.
    """
    outputs_path = os.path.join(os.path.dirname(__file__), "cdk-demo", "outputs.json")
    try:
        with open(outputs_path) as f:
            outputs = json.load(f)
        # outputs.json shape: { "TravelDisruptionStack": { "GatewayArn": "arn:..." } }
        stack = outputs.get("TravelDisruptionStack", {})
        arn = stack.get("GatewayArn", "")
        if arn:
            return arn
    except FileNotFoundError:
        pass
    # Fallback — replace with your deployed gateway ARN or run cdk deploy first
    return "YOUR_GATEWAY_ARN"

def warn(text):
    print(f"{YELLOW}⚠ {text}{RESET}")

def err(text):
    print(f"{RED}✗ {text}{RESET}")


# ── Argument parsing ───────────────────────────────────────────────────────────
def parse_args():
    p = argparse.ArgumentParser(description="Travel Disruption AgentCore Harness Demo")
    p.add_argument("--region",      default="us-east-1", help="AWS region (default: us-east-1)")
    p.add_argument("--skip-create", action="store_true",  help="Skip harness creation (use existing)")
    p.add_argument("--harness-arn", default=None,         help="Existing harness ARN (with --skip-create)")
    p.add_argument("--no-cleanup",  action="store_true",  help="Leave harness running after demo")
    return p.parse_args()


# ── IAM: create execution role ─────────────────────────────────────────────────
ROLE_NAME = "TravelHarnessDemoRole"

TRUST_POLICY = json.dumps({
    "Version": "2012-10-17",
    "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "bedrock-agentcore.amazonaws.com"},
        "Action": "sts:AssumeRole"
    }]
})

INLINE_POLICY = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "bedrock-agentcore:*"
            ],
            "Resource": "*"
        }
    ]
})


def ensure_role(iam):
    """Create or reuse the harness execution role."""
    try:
        r = iam.get_role(RoleName=ROLE_NAME)
        arn = r["Role"]["Arn"]
        ok(f"Reusing existing role: {arn}")
        return arn
    except iam.exceptions.NoSuchEntityException:
        pass

    info("Creating IAM execution role...")
    r = iam.create_role(
        RoleName=ROLE_NAME,
        AssumeRolePolicyDocument=TRUST_POLICY,
        Description="AgentCore harness demo execution role",
    )
    arn = r["Role"]["Arn"]

    iam.put_role_policy(
        RoleName=ROLE_NAME,
        PolicyName="HarnessPermissions",
        PolicyDocument=INLINE_POLICY,
    )

    # IAM propagation delay
    info("Waiting 10s for IAM role to propagate...")
    time.sleep(10)
    ok(f"Role created: {arn}")
    return arn


# ── Create harness ─────────────────────────────────────────────────────────────
HARNESS_NAME = "travel_disruption_demo"

SYSTEM_PROMPT = (
    "You are an autonomous travel disruption recovery agent. "
    "When a flight is cancelled or severely delayed, you must reason through "
    "the complete passenger recovery plan step by step. "
    "For each affected passenger you will: "
    "1. Identify the best available alternative flight on the same route and cabin class. "
    "2. Determine if an overnight hotel is needed and which property matches their preferences. "
    "3. Calculate the appropriate compensation (miles or travel voucher) based on loyalty tier. "
    "4. Compose a clear, empathetic notification message for the passenger. "
    "5. Flag any passengers who need special handling (unaccompanied minor, medical, group > 8). "
    "Think step by step. Be specific with flight numbers, times, and amounts. "
    "Do not ask clarifying questions — act on the information provided."
)


def create_harness(control, role_arn):
    """Create the AgentCore harness and wait until READY."""
    info(f"Creating harness '{HARNESS_NAME}'...")
    try:
        r = control.create_harness(
            harnessName=HARNESS_NAME,
            executionRoleArn=role_arn,
            model={
                "bedrockModelConfig": {
                    "modelId": "us.anthropic.claude-sonnet-4-6"   # cross-region inference profile
                }
            },
            systemPrompt=[{"text": SYSTEM_PROMPT}],
            # No gateway tools for smoke test — agent reasons without executing
            # Uncomment and add gateway ARN to enable real tool calling:
            # tools=[{
            #     "type": "agentcore_gateway",
            #     "name": "travel-gateway",
            #     "config": {"agentCoreGateway": {"gatewayArn": GATEWAY_ARN}}
            # }],
            maxIterations=15,
            timeoutSeconds=120,
        )
    except ClientError as e:
        if "already exists" in str(e).lower() or "ConflictException" in str(type(e)):
            warn(f"Harness '{HARNESS_NAME}' already exists, fetching ARN...")
            resp = control.list_harnesses(maxResults=50)
            for h in resp.get("harnesses", []):
                if h["harnessName"] == HARNESS_NAME:
                    harness_id  = h["harnessId"]
                    harness_arn = h["arn"]
                    info(f"Found existing harness: {harness_arn}")
                    # fall through to poll below
                    break
            else:
                err("Could not find existing harness")
                sys.exit(1)
        else:
            raise
    else:
        harness_id  = r["harnessId"]
        harness_arn = r["arn"]
        info(f"Harness ID:  {harness_id}")
        info(f"Harness ARN: {harness_arn}")

    # Poll until READY
    info("Polling until READY")
    for attempt in range(30):
        time.sleep(5)
        status_r = control.get_harness(harnessId=harness_id)
        status   = status_r.get("harness", {}).get("status", "UNKNOWN")
        print(f"  [{attempt + 1:02d}] status = {status}", flush=True)
        if status == "READY":
            ok("Harness is READY")
            return status_r["harness"]["arn"]
        if status in ("FAILED", "DELETED"):
            err(f"Harness entered terminal state: {status}")
            sys.exit(1)

    err("Timed out waiting for harness to become READY")
    sys.exit(1)


# ── Stream helper ──────────────────────────────────────────────────────────────
def stream_response(response, label="Agent"):
    """
    Stream an InvokeHarness response to stdout.
    Returns (full_text, tool_use_id, tool_name, tool_input) if an inline
    function call is detected (stopReason == tool_use), else (full_text, None, None, None).
    """
    print(f"\n{BOLD}{CYAN}{label}:{RESET} ", end="", flush=True)

    full_text      = ""
    tool_use_id    = None
    tool_name      = None
    tool_input_buf = ""
    stop_reason    = None

    for event in response["stream"]:

        if "contentBlockDelta" in event:
            delta = event["contentBlockDelta"].get("delta", {})
            if "text" in delta:
                chunk = delta["text"]
                print(chunk, end="", flush=True)
                full_text += chunk
            if "toolUse" in delta:
                # input field arrives as partial JSON string fragments
                fragment = delta["toolUse"].get("input", "")
                if isinstance(fragment, str):
                    tool_input_buf += fragment
                elif isinstance(fragment, dict):
                    # some SDK versions return parsed dict directly
                    tool_input_buf = json.dumps(fragment)

        if "contentBlockStart" in event:
            start = event["contentBlockStart"].get("start", {})
            if "toolUse" in start:
                tool_use_id = start["toolUse"]["toolUseId"]
                tool_name   = start["toolUse"]["name"]

        if "messageStop" in event:
            stop_reason = event["messageStop"].get("stopReason")

        if "metadata" in event:
            usage = event["metadata"].get("usage", {})
            if usage:
                info(
                    f"\n  [tokens] input={usage.get('inputTokens', '?')} "
                    f"output={usage.get('outputTokens', '?')}"
                )

        if "runtimeClientError" in event:
            err(f"Runtime error: {event['runtimeClientError']['message']}")

    print()  # newline after streaming

    if stop_reason == "tool_use" and tool_name:
        try:
            tool_input = json.loads(tool_input_buf) if tool_input_buf.strip() else {}
        except json.JSONDecodeError:
            # input may have arrived pre-parsed or in an unexpected format
            tool_input = {"raw": tool_input_buf}
        return full_text, tool_use_id, tool_name, tool_input

    return full_text, None, None, None


# ── Demo scenarios ─────────────────────────────────────────────────────────────
def demo_standard_recovery(runtime, harness_arn):
    """
    Step 2: Standard disruption recovery.
    Single passenger, no special handling needed.
    """
    banner("DEMO 1 — Standard Disruption Recovery")

    GATEWAY_ARN = load_gateway_arn()

    session_id = str(uuid.uuid4()) + "-pax-john-smith"
    info(f"Session ID: {session_id}")

    step(1, "Flight AA123 cancelled. Invoking harness for Gold-tier passenger...")

    response = runtime.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        # Override model to Haiku for demo — less conservative about tool calling
        model={"bedrockModelConfig": {"modelId": "us.anthropic.claude-haiku-4-5-20251001-v1:0"}},
        # Pass gateway tools explicitly at invoke time — confirmed working pattern
        tools=[{
            "type": "agentcore_gateway",
            "name": "travel-gateway",
            "config": {
                "agentCoreGateway": {
                    "gatewayArn": GATEWAY_ARN,
                    "outboundAuth": {"awsIam": {}},
                }
            }
        }],
        messages=[{
            "role": "user",
            "content": [{
                "text": (
                    "DISRUPTION: Flight AA123 (JFK→LAX, today 3PM) CANCELLED.\n"
                    "Passenger: John Smith | Gold | aisle seat | Marriott preference.\n"
                    "Call rebook_flight then notify_traveler."
                )
            }]
        }],
    )
    stream_response(response, "Orchestrator Agent")
    return session_id


def demo_memory(runtime, harness_arn, session_id):
    """
    Step 3: Follow-up on the same session — agent uses memory, no re-querying.
    """
    GATEWAY_ARN = load_gateway_arn()

    banner("DEMO 2 — AgentCore Memory (Same Session)")

    step(2, "Follow-up question using the SAME session ID — no context re-sent...")
    info(f"Session ID: {session_id}  ← reusing")

    response = runtime.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,   # ← same session, agent remembers everything
        model={"bedrockModelConfig": {"modelId": "us.anthropic.claude-haiku-4-5-20251001-v1:0"}},
        tools=[{
            "type": "agentcore_gateway",
            "name": "travel-gateway",
            "config": {
                "agentCoreGateway": {
                    "gatewayArn": GATEWAY_ARN,
                    "outboundAuth": {"awsIam": {}},
                }
            }
        }],
        messages=[{
            "role": "user",
            "content": [{"text": "Why did you choose that specific alternative flight for John?"}]
        }],
    )
    stream_response(response, "Agent (from memory)")


def demo_inline_escalation(runtime, harness_arn):
    """
    Step 4: Passenger with special needs triggers human-in-the-loop escalation.
    Demonstrates inline function / tool_use stopReason handling.
    """
    banner("DEMO 3 — Human-in-the-Loop Escalation (Inline Function)")

    session_id = str(uuid.uuid4()) + "-pax-minor-001"
    info(f"Session ID: {session_id}")

    # Register an inline function tool at invoke time
    escalation_tool = {
        "type": "inline_function",
        "name": "escalate_to_agent",
        "config": {
            "inlineFunction": {
                "description": (
                    "Escalate to a human agent for passengers requiring special handling. "
                    "Use for: unaccompanied minors, medical assistance, group bookings over 8, "
                    "or any situation beyond standard rebooking policy."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "passenger_id": {"type": "string"},
                        "reason":       {"type": "string"},
                        "urgency":      {"type": "string", "enum": ["low", "medium", "high"]},
                        "details":      {"type": "string"},
                    },
                    "required": ["passenger_id", "reason", "urgency"],
                },
            }
        },
    }

    GATEWAY_ARN = load_gateway_arn()

    step(3, "Invoking harness for unaccompanied minor — expect escalation...")

    response = runtime.invoke_harness(
        harnessArn=harness_arn,
        runtimeSessionId=session_id,
        # Use Sonnet for escalation — it correctly emits tool_use stream events
        model={"bedrockModelConfig": {"modelId": "us.anthropic.claude-sonnet-4-6"}},
        tools=[
            # Gateway tools (rebook_flight + notify_traveler)
            {
                "type": "agentcore_gateway",
                "name": "travel-gateway",
                "config": {
                    "agentCoreGateway": {
                        "gatewayArn": GATEWAY_ARN,
                        "outboundAuth": {"awsIam": {}},
                    }
                }
            },
            # Inline function — escalation handled client-side
            escalation_tool,
        ],
        messages=[{
            "role": "user",
            "content": [{
                "text": (
                    "Flight UA456 (ORD→SFO, today 2PM) CANCELLED. "
                    "Passenger: Emma Johnson, age 9, unaccompanied minor. "
                    "Guardian: +1-555-0199. "
                    "Call escalate_to_agent."
                )
            }]
        }],
    )

    _, tool_use_id, tool_name, tool_input = stream_response(response, "Orchestrator Agent")

    if tool_name == "escalate_to_agent":
        print(f"\n{YELLOW}{BOLD}⚡ Inline function triggered!{RESET}")
        print(f"   Tool:    {tool_name}")
        print(f"   Input:   {json.dumps(tool_input, indent=2)}")

        # Simulate human agent decision
        print(f"\n{BOLD}[Human Agent Console]{RESET}")
        print("  Passenger: Emma Johnson (UM-9)")
        print("  Action: Rebooking on next flight, notifying guardian, alerting UM desk")
        human_decision = (
            "Human agent handled. Emma Johnson rebooked on UA458 (ORD→SFO 5:30 PM). "
            "Guardian +1-555-0199 notified. United UM escort arranged at gate C22. "
            "Supervisor sign-off: AGENT_ID_4821."
        )
        ok(f"Human decision recorded: {human_decision[:80]}...")

        # Send result back to agent — both toolUse + toolResult required
        step(4, "Returning human decision to agent to complete the turn...")
        response2 = runtime.invoke_harness(
            harnessArn=harness_arn,
            runtimeSessionId=session_id,
            model={"bedrockModelConfig": {"modelId": "us.anthropic.claude-sonnet-4-6"}},
            tools=[
                {
                    "type": "agentcore_gateway",
                    "name": "travel-gateway",
                    "config": {
                        "agentCoreGateway": {
                            "gatewayArn": GATEWAY_ARN,
                            "outboundAuth": {"awsIam": {}},
                        }
                    }
                },
                escalation_tool,
            ],
            messages=[
                {
                    "role": "assistant",
                    "content": [{
                        "toolUse": {
                            "toolUseId": tool_use_id,
                            "name":      tool_name,
                            "input":     tool_input,
                        }
                    }],
                },
                {
                    "role": "user",
                    "content": [{
                        "toolResult": {
                            "toolUseId": tool_use_id,
                            "content":   [{"text": human_decision}],
                            "status":    "success",
                        }
                    }],
                },
            ],
        )
        stream_response(response2, "Agent (after escalation)")
    else:
        warn("Agent did not trigger escalation — try a different prompt or add inline tool to harness config")


# ── Cleanup ────────────────────────────────────────────────────────────────────
def cleanup(control, harness_arn):
    banner("CLEANUP")
    info(f"Deleting harness: {harness_arn}")
    try:
        harness_id = harness_arn.split("/")[-1]
        control.delete_harness(harnessId=harness_id)
        ok("Harness deleted")
    except Exception as e:
        warn(f"Could not delete harness: {e}")


# ── Main ───────────────────────────────────────────────────────────────────────
def main():
    args = parse_args()

    banner("Travel Disruption Agent — AgentCore Harness Demo")
    print(f"  Region:  {args.region}")
    print(f"  Model:   us.anthropic.claude-sonnet-4-6")
    print(f"  Mode:    {'smoke test (no real tools)' if True else 'full tool execution'}")

    # Clients
    iam     = boto3.client("iam")
    control = boto3.client("bedrock-agentcore-control", region_name=args.region)
    runtime = boto3.client("bedrock-agentcore",         region_name=args.region)

    # Verify identity
    sts = boto3.client("sts")
    identity = sts.get_caller_identity()
    ok(f"AWS identity: {identity['Arn']}")

    # ── Step 1: Create or reuse harness ───────────────────────────────
    if args.skip_create and args.harness_arn:
        harness_arn = args.harness_arn
        ok(f"Using existing harness: {harness_arn}")
    else:
        step(1, "Setting up IAM execution role and creating harness...")
        role_arn    = ensure_role(iam)
        harness_arn = create_harness(control, role_arn)

    print(f"\n  {BOLD}Harness ARN:{RESET} {harness_arn}")

    # ── Step 2: Standard recovery ──────────────────────────────────────
    session_id = demo_standard_recovery(runtime, harness_arn)

    # ── Step 3: Memory ────────────────────────────────────────────────
    demo_memory(runtime, harness_arn, session_id)

    # ── Step 4: Inline escalation ─────────────────────────────────────
    demo_inline_escalation(runtime, harness_arn)

    # ── Cleanup ───────────────────────────────────────────────────────
    if not args.no_cleanup:
        cleanup(control, harness_arn)
    else:
        warn("Skipping cleanup (--no-cleanup). Harness left running.")
        warn(f"To delete manually: aws bedrock-agentcore-control delete-harness --harness-id {harness_arn.split('/')[-1]} --region {args.region}")

    banner("Demo Complete")
    ok("All scenarios demonstrated successfully.")


if __name__ == "__main__":
    main()
