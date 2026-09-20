from __future__ import annotations

import re
from typing import Literal

RequestIntent = Literal[
    "conversation", "travel_plan", "flight_search", "hotel_search", "time", "filesystem"
]

_FLIGHT_PATTERN = re.compile(r"\b(?:flight|flights|fly|airfare)\b", re.IGNORECASE)
_HOTEL_PATTERN = re.compile(r"\b(?:hotel|hotels|stay|stays|accommodation)\b", re.IGNORECASE)

_TIME_PATTERN = re.compile(
    r"\b(?:current\s+(?:date|time)|what(?:'s|\s+is)\s+the\s+(?:date|time)|"
    r"time\s+(?:is\s+it\s+)?in|timezone|convert\s+.+\s+time)\b",
    re.IGNORECASE,
)
_FILESYSTEM_PATTERN = re.compile(
    r"\b(?:file|files|folder|directory|workspace)\b.*\b(?:list|read|show|inspect|open|contents?)\b|"
    r"\b(?:list|read|show|inspect|open)\b.*\b(?:file|files|folder|directory|workspace)\b",
    re.IGNORECASE,
)
_TRAVEL_PLAN_PATTERN = re.compile(
    r"\b(?:plan|itinerary|schedule|organize|arrange|build)\b.{0,50}\b"
    r"(?:trip|travel|holiday|vacation|visit|days?|nights?)\b|"
    r"\b(?:trip|travel|holiday|vacation|itinerary)\b.{0,50}\b"
    r"(?:to|in|for|plan|schedule)\b|"
    r"\b\d+\s*(?:day|days|night|nights)\s+(?:in|to)\b",
    re.IGNORECASE,
)


def classify_request(text: str) -> RequestIntent:
    normalized = " ".join(text.split())
    if _FLIGHT_PATTERN.search(normalized):
        return "flight_search"
    if _HOTEL_PATTERN.search(normalized):
        return "hotel_search"
    if _TIME_PATTERN.search(normalized):
        return "time"
    if _FILESYSTEM_PATTERN.search(normalized):
        return "filesystem"
    if _TRAVEL_PLAN_PATTERN.search(normalized):
        return "travel_plan"
    return "conversation"
