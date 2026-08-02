"""
Notify Agent Lambda — Mock Traveler Notification Tool
=====================================================
Exposed as an MCP tool via AgentCore Gateway.
The agent calls: notify_traveler(passenger_id, channel, subject, message,
                                 contact, new_flight, confirmation_number)

Mock behaviour: logs the notification and returns a delivery receipt.
In a real deployment this would publish to Amazon SNS (SMS) and
Amazon SES (email) with the passenger's actual contact details.
"""
import json
import logging
import os
import random
import string
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Optionally publish to a real SNS topic if env var is set
SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "")


def generate_message_id() -> str:
    return "MSG-" + "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def send_notification(
    passenger_id: str,
    channel: str,          # "sms", "email", "push", or "all"
    subject: str,
    message: str,
    contact: str = "",     # phone or email address
    new_flight: str = "",
    confirmation_number: str = "",
) -> dict:
    """
    Send a notification to the traveler.
    Returns delivery receipt with message ID and timestamp.
    """
    timestamp   = datetime.now(timezone.utc).isoformat()
    message_id  = generate_message_id()
    channel     = channel.lower()

    # Build the full notification payload
    payload = {
        "passenger_id":        passenger_id,
        "channel":             channel,
        "subject":             subject,
        "message":             message,
        "contact":             contact or f"on-file-for-{passenger_id}",
        "new_flight":          new_flight,
        "confirmation_number": confirmation_number,
        "sent_at":             timestamp,
        "message_id":          message_id,
    }

    logger.info("Sending notification: %s", json.dumps(payload))

    # Publish to real SNS topic if configured (optional)
    if SNS_TOPIC_ARN:
        try:
            sns = boto3.client("sns")
            sns.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=subject,
                Message=json.dumps(payload, indent=2),
                MessageAttributes={
                    "passenger_id": {
                        "DataType": "String",
                        "StringValue": passenger_id,
                    },
                    "channel": {
                        "DataType": "String",
                        "StringValue": channel,
                    },
                },
            )
            logger.info("Published to SNS topic: %s", SNS_TOPIC_ARN)
        except Exception as e:
            # Non-fatal — log and continue with mock response
            logger.warning("SNS publish failed (non-fatal): %s", e)

    # Build delivery receipt
    channels_sent = []
    if channel in ("sms", "all"):
        channels_sent.append({
            "type": "SMS",
            "status": "DELIVERED",
            "contact": contact or "+1-XXX-XXX-XXXX (on file)",
            "message_id": message_id + "-SMS",
        })
    if channel in ("email", "all"):
        channels_sent.append({
            "type": "EMAIL",
            "status": "DELIVERED",
            "contact": contact or "email-on-file",
            "subject": subject,
            "message_id": message_id + "-EMAIL",
        })
    if channel in ("push", "all"):
        channels_sent.append({
            "type": "PUSH",
            "status": "DELIVERED",
            "message_id": message_id + "-PUSH",
        })
    if not channels_sent:
        # fallback
        channels_sent.append({
            "type": channel.upper(),
            "status": "DELIVERED",
            "message_id": message_id,
        })

    result = {
        "status": "SENT",
        "message_id": message_id,
        "passenger_id": passenger_id,
        "channels": channels_sent,
        "sent_at": timestamp,
        "message_preview": message[:120] + ("..." if len(message) > 120 else ""),
        "summary": (
            f"Notification sent to {passenger_id} via {channel.upper()}. "
            f"Message ID: {message_id}. "
            f"Content: {subject}."
        ),
    }

    logger.info("Notification result: %s", json.dumps(result))
    return result


def lambda_handler(event, context):
    """
    AgentCore Gateway Lambda target handler.
    The gateway passes tool input properties directly as the event object.
    """
    logger.info("Event: %s", json.dumps(event))

    try:
        result = send_notification(
            passenger_id        = event.get("passenger_id", "UNKNOWN"),
            channel             = event.get("channel", "all"),
            subject             = event.get("subject", "Your flight update"),
            message             = event.get("message", ""),
            contact             = event.get("contact", ""),
            new_flight          = event.get("new_flight", ""),
            confirmation_number = event.get("confirmation_number", ""),
        )
        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }
    except Exception as e:
        logger.exception("Error in notify_traveler")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "ERROR",
                "message": str(e),
            }),
        }
