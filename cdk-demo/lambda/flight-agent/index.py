"""
Flight Agent Lambda — Mock GDS Rebooking Tool
=============================================
Exposed as an MCP tool via AgentCore Gateway.
The agent calls: rebook_flight(passenger_id, origin, destination,
                               original_flight, cabin_class, max_hours)

Mock behaviour: generates a realistic-looking next available flight
based on the input. In a real deployment this would call the airline
GDS API (Amadeus, Sabre, etc.) via the AgentCore Gateway connector.
"""
import json
import logging
import random
import string
from datetime import datetime, timedelta, timezone

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Mock flight inventory — next available flights per route
MOCK_FLIGHTS = {
    ("JFK", "LAX"): [
        {"flight": "AA457", "dep": "17:30", "arr": "20:45", "duration": "5h15m"},
        {"flight": "AA891", "dep": "19:00", "arr": "22:10", "duration": "5h10m"},
        {"flight": "DL204", "dep": "20:15", "arr": "23:30", "duration": "5h15m"},
    ],
    ("ORD", "SFO"): [
        {"flight": "UA458", "dep": "17:30", "arr": "20:15", "duration": "4h45m"},
        {"flight": "UA672", "dep": "19:00", "arr": "21:45", "duration": "4h45m"},
        {"flight": "AA302", "dep": "20:30", "arr": "23:15", "duration": "4h45m"},
    ],
    ("BOS", "MIA"): [
        {"flight": "AA1143", "dep": "16:45", "arr": "20:15", "duration": "3h30m"},
        {"flight": "DL981",  "dep": "18:00", "arr": "21:30", "duration": "3h30m"},
    ],
}

# Default fallback for unknown routes
DEFAULT_FLIGHTS = [
    {"flight": "XX100", "dep": "17:00", "arr": "20:00", "duration": "3h00m"},
    {"flight": "XX200", "dep": "19:00", "arr": "22:00", "duration": "3h00m"},
]

# Cabin class → seat map stub
SEAT_MAP = {
    "economy":  ["22C", "28A", "34C", "41F"],
    "business": ["3A",  "4C",  "5A"],
    "first":    ["1A",  "2C"],
}


def generate_confirmation() -> str:
    """Generate a realistic-looking booking confirmation code."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))


def rebook_flight(
    passenger_id: str,
    origin: str,
    destination: str,
    original_flight: str,
    cabin_class: str,
    max_hours: int = 8,
) -> dict:
    """
    Find and confirm the next available flight.
    Returns rebooking confirmation or error details.
    """
    origin      = origin.upper()
    destination = destination.upper()
    cabin_class = cabin_class.lower()

    route_key = (origin, destination)
    candidates = MOCK_FLIGHTS.get(route_key, DEFAULT_FLIGHTS)

    # Pick the first available flight within max_hours window
    # (in production: filter by actual departure time vs. now + max_hours)
    selected = candidates[0]

    # Pick an aisle seat (type C or A) if economy, else best available
    available_seats = SEAT_MAP.get(cabin_class, SEAT_MAP["economy"])
    seat = random.choice(available_seats)

    confirmation = generate_confirmation()

    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = {
        "status": "CONFIRMED",
        "confirmation_number": confirmation,
        "passenger_id": passenger_id,
        "original_flight": original_flight,
        "new_flight": {
            "flight_number": selected["flight"],
            "origin": origin,
            "destination": destination,
            "departure_date": today,
            "departure_time": selected["dep"],
            "arrival_time": selected["arr"],
            "duration": selected["duration"],
            "cabin_class": cabin_class,
            "seat": seat,
            "gate": f"{random.choice('ABCDE')}{random.randint(1, 30)}",
            "terminal": str(random.randint(1, 8)),
        },
        "rebooking_fee": 0,          # waived for involuntary cancellation
        "fare_difference": 0,        # protected fare — no additional charge
        "message": (
            f"Passenger {passenger_id} successfully rebooked from "
            f"{original_flight} onto {selected['flight']} "
            f"({origin}→{destination}, {selected['dep']} → {selected['arr']}). "
            f"Seat {seat} confirmed. Confirmation: {confirmation}."
        ),
    }

    logger.info("Rebooked: %s", json.dumps(result))
    return result


def lambda_handler(event, context):
    """
    AgentCore Gateway Lambda target handler.
    The gateway passes tool input properties directly as the event object.
    e.g. event = {"passenger_id": "...", "origin": "JFK", ...}
    """
    logger.info("Event: %s", json.dumps(event))

    try:
        result = rebook_flight(
            passenger_id    = event.get("passenger_id", "UNKNOWN"),
            origin          = event.get("origin", "???"),
            destination     = event.get("destination", "???"),
            original_flight = event.get("original_flight", "???"),
            cabin_class     = event.get("cabin_class", "economy"),
            max_hours       = int(event.get("max_hours", 8)),
        )
        return {
            "statusCode": 200,
            "body": json.dumps(result),
        }
    except Exception as e:
        logger.exception("Error in rebook_flight")
        return {
            "statusCode": 500,
            "body": json.dumps({
                "status": "ERROR",
                "message": str(e),
            }),
        }
