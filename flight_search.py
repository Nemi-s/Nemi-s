"""
Flight Search Tool — YYZ to BOM (Toronto → Mumbai)
Searches for business class flights with up to 1 stop using the Amadeus Test API.

Usage:
    pip install amadeus requests
    python flight_search.py

Set environment variables before running:
    export AMADEUS_CLIENT_ID=your_client_id
    export AMADEUS_CLIENT_SECRET=your_client_secret

Get free API keys at: https://developers.amadeus.com/register
"""

import os
import json
import requests
from datetime import datetime, date

AMADEUS_BASE = "https://test.api.amadeus.com"


def get_token(client_id: str, client_secret: str) -> str:
    resp = requests.post(
        f"{AMADEUS_BASE}/v1/security/oauth2/token",
        data={
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def search_flights(
    token: str,
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 2,
    travel_class: str = "BUSINESS",
    max_stops: int = 1,
    currency: str = "CAD",
    max_results: int = 10,
) -> list[dict]:
    headers = {"Authorization": f"Bearer {token}"}
    params = {
        "originLocationCode": origin,
        "destinationLocationCode": destination,
        "departureDate": departure_date,
        "adults": adults,
        "travelClass": travel_class,
        "nonStop": "false",
        "currencyCode": currency,
        "max": max_results,
    }
    resp = requests.get(
        f"{AMADEUS_BASE}/v2/shopping/flight-offers", headers=headers, params=params
    )
    resp.raise_for_status()
    offers = resp.json().get("data", [])

    # Filter to max 1 stop per itinerary
    filtered = []
    for offer in offers:
        itinerary = offer["itineraries"][0]
        if len(itinerary["segments"]) - 1 <= max_stops:
            filtered.append(offer)
    return filtered


def format_duration(iso_duration: str) -> str:
    """Convert PT19H40M → 19h 40m"""
    iso_duration = iso_duration.replace("PT", "")
    hours = minutes = 0
    if "H" in iso_duration:
        h, iso_duration = iso_duration.split("H")
        hours = int(h)
    if "M" in iso_duration:
        m = iso_duration.replace("M", "")
        minutes = int(m)
    return f"{hours}h {minutes}m"


def display_results(offers: list[dict]) -> None:
    if not offers:
        print("No flights found matching your criteria.")
        return

    print(f"\n{'='*70}")
    print(f"  Business Class Flights: YYZ → BOM  |  2 Adults  |  Max 1 Stop")
    print(f"{'='*70}\n")

    for i, offer in enumerate(offers, 1):
        price = offer["price"]
        total = float(price["total"])
        currency = price["currency"]
        per_person = total / 2

        itinerary = offer["itineraries"][0]
        segments = itinerary["segments"]
        stops = len(segments) - 1
        total_duration = format_duration(itinerary["duration"])

        dep = segments[0]["departure"]
        arr = segments[-1]["arrival"]
        dep_time = datetime.fromisoformat(dep["at"]).strftime("%d %b %H:%M")
        arr_time = datetime.fromisoformat(arr["at"]).strftime("%d %b %H:%M")

        via = " → ".join(s["arrival"]["iataCode"] for s in segments[:-1])
        carrier = segments[0]["carrierCode"]

        stop_label = "Non-stop" if stops == 0 else f"{stops} stop ({'via ' + via})"

        print(f"  Option {i}  |  {carrier}  |  {stop_label}")
        print(f"  {dep_time} (YYZ)  →  {arr_time} (BOM)  |  Total: {total_duration}")
        print(f"  Price: {currency} {total:,.0f} total  ({currency} {per_person:,.0f}/person)")
        print(f"  {'-'*60}")

    print()
    cheapest = min(offers, key=lambda o: float(o["price"]["total"]))
    best_price = float(cheapest["price"]["total"])
    currency = cheapest["price"]["currency"]
    print(f"  Cheapest option: {currency} {best_price:,.0f} total ({currency} {best_price/2:,.0f}/person)")
    print(f"{'='*70}\n")


def main():
    client_id = os.environ.get("AMADEUS_CLIENT_ID")
    client_secret = os.environ.get("AMADEUS_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Set AMADEUS_CLIENT_ID and AMADEUS_CLIENT_SECRET environment variables.\n"
            "Get free keys at: https://developers.amadeus.com/register\n"
        )
        print("Showing sample search parameters instead:\n")
        print("  Origin:        YYZ (Toronto Pearson)")
        print("  Destination:   BOM (Mumbai Chhatrapati Shivaji)")
        print("  Dates:         June 28, 2026  |  June 29, 2026")
        print("  Passengers:    2 Adults")
        print("  Cabin:         Business Class")
        print("  Max Stops:     1")
        print("  Currency:      CAD")
        return

    try:
        print("Authenticating with Amadeus API...")
        token = get_token(client_id, client_secret)
        print("Authentication successful.\n")

        for travel_date in ["2026-06-28", "2026-06-29"]:
            print(f"Searching flights for {travel_date}...")
            offers = search_flights(
                token=token,
                origin="YYZ",
                destination="BOM",
                departure_date=travel_date,
                adults=2,
                travel_class="BUSINESS",
                max_stops=1,
                currency="CAD",
                max_results=10,
            )
            print(f"\nResults for {travel_date}:")
            display_results(offers)

    except requests.HTTPError as e:
        print(f"API error: {e.response.status_code} — {e.response.text}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
