from __future__ import annotations

import json
from datetime import date, timedelta
from functools import cache
from pathlib import Path
from typing import Any

DATA_DIRECTORY = Path(__file__).with_name("data")
FIXTURE_NOTICE = (
    "Fixture data only. Airport identities are real, but schedules, availability, "
    "hotel listings, and prices are simulated and are not bookable."
)


@cache
def _load_json(name: str) -> list[dict[str, Any]]:
    with (DATA_DIRECTORY / name).open(encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, list):
        raise ValueError(f"{name} must contain a JSON array.")
    return value


def _iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field} must use YYYY-MM-DD format.") from exc


def _airport(value: str) -> dict[str, Any] | None:
    needle = value.strip().casefold()
    if not needle:
        return None
    exact = [
        airport
        for airport in _load_json("airports.json")
        if needle in {airport["iata"].casefold(), airport["city"].casefold()}
    ]
    if exact:
        return exact[0]
    return next(
        (
            airport
            for airport in _load_json("airports.json")
            if needle in airport["name"].casefold()
        ),
        None,
    )


def list_airports(region: str = "all") -> dict[str, Any]:
    """Return supported airport identities, optionally filtered to India or international."""
    normalized = region.strip().casefold()
    if normalized not in {"all", "india", "international"}:
        raise ValueError("region must be all, india, or international.")
    airports = _load_json("airports.json")
    if normalized == "india":
        airports = [item for item in airports if item["country_code"] == "IN"]
    elif normalized == "international":
        airports = [item for item in airports if item["country_code"] != "IN"]
    return {"status": "ok", "fixture": True, "airports": airports, "notice": FIXTURE_NOTICE}


def search_flights(
    origin: str,
    destination: str,
    departure_date: str,
    adults: int = 1,
) -> dict[str, Any]:
    """Search recurring flight fixtures and project them onto the requested date."""
    if not 1 <= adults <= 9:
        raise ValueError("adults must be between 1 and 9.")
    requested_date = _iso_date(departure_date, "departure_date")
    origin_airport = _airport(origin)
    destination_airport = _airport(destination)
    if origin_airport is None or destination_airport is None:
        return {
            "status": "unsupported_airport",
            "fixture": True,
            "origin": origin,
            "destination": destination,
            "notice": FIXTURE_NOTICE,
        }

    results: list[dict[str, Any]] = []
    for template in _load_json("flights.json"):
        if template["origin"] != origin_airport["iata"]:
            continue
        if template["destination"] != destination_airport["iata"]:
            continue
        arrival_date = requested_date + timedelta(days=int(template["arrival_day_offset"]))
        price_per_adult = int(template["price_inr"])
        results.append(
            {
                "fixture_id": template["fixture_id"],
                "airline": template["airline"],
                "flight_number": template["flight_number"],
                "origin": origin_airport,
                "destination": destination_airport,
                "departure_at": f"{requested_date.isoformat()}T{template['departure_time']}:00",
                "arrival_at": f"{arrival_date.isoformat()}T{template['arrival_time']}:00",
                "duration_minutes": int(template["duration_minutes"]),
                "stops": int(template["stops"]),
                "aircraft": template["aircraft"],
                "price": {
                    "currency": "INR",
                    "per_adult": price_per_adult,
                    "total": price_per_adult * adults,
                },
                "seats_requested": adults,
                "available": adults <= int(template["fixture_seats"]),
            }
        )
    results.sort(key=lambda item: item["price"]["total"])
    return {
        "status": "ok" if results else "no_fixture_route",
        "fixture": True,
        "query": {
            "origin": origin_airport["iata"],
            "destination": destination_airport["iata"],
            "departure_date": requested_date.isoformat(),
            "adults": adults,
        },
        "flights": results,
        "notice": FIXTURE_NOTICE,
    }


def list_routes() -> dict[str, Any]:
    """List the origin and destination pairs available in the fixture catalog."""
    routes = sorted({(item["origin"], item["destination"]) for item in _load_json("flights.json")})
    return {
        "status": "ok",
        "fixture": True,
        "routes": [
            {"origin": origin, "destination": destination} for origin, destination in routes
        ],
        "notice": FIXTURE_NOTICE,
    }


def search_hotels(
    city: str,
    check_in: str,
    check_out: str,
    guests: int = 1,
    rooms: int = 1,
) -> dict[str, Any]:
    """Search hotel fixtures and calculate a stay price for the requested dates."""
    if not 1 <= guests <= 12:
        raise ValueError("guests must be between 1 and 12.")
    if not 1 <= rooms <= 5:
        raise ValueError("rooms must be between 1 and 5.")
    check_in_date = _iso_date(check_in, "check_in")
    check_out_date = _iso_date(check_out, "check_out")
    nights = (check_out_date - check_in_date).days
    if nights < 1:
        raise ValueError("check_out must be after check_in.")

    needle = city.strip().casefold()
    results: list[dict[str, Any]] = []
    for hotel in _load_json("hotels.json"):
        if needle not in {hotel["city"].casefold(), hotel["city_code"].casefold()}:
            continue
        nightly_rate = int(hotel["nightly_rate_inr"])
        results.append(
            {
                **hotel,
                "check_in": check_in_date.isoformat(),
                "check_out": check_out_date.isoformat(),
                "nights": nights,
                "rooms": rooms,
                "guests": guests,
                "available": guests <= int(hotel["max_guests_per_room"]) * rooms,
                "price": {
                    "currency": "INR",
                    "nightly_per_room": nightly_rate,
                    "total": nightly_rate * nights * rooms,
                },
            }
        )
    results.sort(key=lambda item: item["price"]["total"])
    return {
        "status": "ok" if results else "unsupported_city",
        "fixture": True,
        "query": {
            "city": city,
            "check_in": check_in_date.isoformat(),
            "check_out": check_out_date.isoformat(),
            "guests": guests,
            "rooms": rooms,
        },
        "hotels": results,
        "notice": FIXTURE_NOTICE,
    }


def get_hotel(hotel_id: str) -> dict[str, Any]:
    """Return one fixture hotel by its stable ID."""
    hotel = next(
        (item for item in _load_json("hotels.json") if item["hotel_id"] == hotel_id.strip()),
        None,
    )
    return {
        "status": "ok" if hotel else "not_found",
        "fixture": True,
        "hotel": hotel,
        "notice": FIXTURE_NOTICE,
    }


def list_hotel_cities() -> dict[str, Any]:
    """List cities represented in the hotel fixture catalog."""
    cities = sorted({(item["city"], item["country_code"]) for item in _load_json("hotels.json")})
    return {
        "status": "ok",
        "fixture": True,
        "cities": [{"city": city, "country_code": country} for city, country in cities],
        "notice": FIXTURE_NOTICE,
    }
