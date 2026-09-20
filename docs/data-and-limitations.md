# Fixture dataset contract and limitations

## Dataset identity

This repository contains a small, manually curated JSON fixture catalog made specifically for
deterministic MCP and A2A interoperability tests. It is not imported from an airline, hotel,
global distribution system, government feed, or other third-party travel dataset.

Airport names, IATA codes, cities, country codes, and time zones identify real-world locations.
Everything that represents a travel offer is simulated: airlines, flight numbers, schedules,
aircraft, seats, prices, hotel properties, ratings, amenities, and availability. Nothing returned
by this project can be booked or presented as a live offer.

The catalog is primarily India-centric. It covers several major Indian cities, selected domestic
routes, and outbound routes from India to a small set of international hubs.

## Coverage summary

| Catalog | Coverage |
|---|---|
| Airports | 16 airports: 8 in India and 8 international |
| Flight templates | 15 fixtures over 14 directional origin/destination pairs |
| Hotel fixtures | 12 properties in 10 cities |
| Currency | All flight and hotel prices are simulated INR values |

## Airports

An airport appearing here means that its code or city can be recognized. It does not guarantee
that a flight fixture exists for every pair of recognized airports.

### India

| IATA | City | Airport |
|---|---|---|
| `DEL` | Delhi | Indira Gandhi International Airport |
| `BOM` | Mumbai | Chhatrapati Shivaji Maharaj International Airport |
| `BLR` | Bengaluru | Kempegowda International Airport |
| `MAA` | Chennai | Chennai International Airport |
| `HYD` | Hyderabad | Rajiv Gandhi International Airport |
| `CCU` | Kolkata | Netaji Subhas Chandra Bose International Airport |
| `GOI` | Goa | Dabolim Airport |
| `COK` | Kochi | Cochin International Airport |

### International

| IATA | City | Country | Airport |
|---|---|---|---|
| `DXB` | Dubai | United Arab Emirates | Dubai International Airport |
| `SIN` | Singapore | Singapore | Singapore Changi Airport |
| `LHR` | London | United Kingdom | Heathrow Airport |
| `CDG` | Paris | France | Charles de Gaulle Airport |
| `JFK` | New York | United States | John F. Kennedy International Airport |
| `NRT` | Tokyo | Japan | Narita International Airport |
| `SYD` | Sydney | Australia | Sydney Airport |
| `FRA` | Frankfurt | Germany | Frankfurt Airport |

## Flight routes

Routes are directional. A listed outbound route does not imply that its reverse is available.

| Region | Included directional routes |
|---|---|
| India domestic | `DEL→BOM`, `BOM→DEL`, `BLR→DEL`, `DEL→BLR`, `BOM→GOI` |
| India to international | `DEL→DXB`, `BOM→DXB`, `DEL→LHR`, `DEL→CDG`, `BOM→SIN`, `DEL→JFK`, `BLR→FRA`, `DEL→NRT`, `DEL→SYD` |

`DEL→BOM` has two flight fixtures; each other route has one. This produces 15 flight results
templates across 14 route pairs.

## Hotel cities

| Region | City | Code | Fixture properties |
|---|---|---|---:|
| India | Delhi | `DEL` | 2 |
| India | Mumbai | `BOM` | 2 |
| India | Bengaluru | `BLR` | 1 |
| India | Goa | `GOI` | 1 |
| International | Dubai | `DXB` | 1 |
| International | Singapore | `SIN` | 1 |
| International | London | `LHR` | 1 |
| International | Paris | `CDG` | 1 |
| International | New York | `JFK` | 1 |
| International | Tokyo | `NRT` | 1 |

## Date and price behavior

Flight fixtures are recurring templates rather than dated inventory. A search accepts an ISO
`YYYY-MM-DD` departure date and projects the fixture's local departure and arrival times onto that
date. The explicit arrival-day offset moves overnight arrivals to the next calendar day. There is
no catalog expiry date, so valid dates in later years continue to work for testing; this does not
claim real future availability or pricing.

Hotel searches accept valid check-in and check-out dates, with check-out strictly after check-in.
The returned stay total is the simulated nightly rate multiplied by the number of nights and
rooms. All prices are in INR and are stable fixture values, with no taxes, fees, exchange rates,
demand pricing, or seasonal changes.

Flight searches accept 1–9 adults. Hotel searches accept 1–12 guests and 1–5 rooms, subject to
each fixture property's per-room guest capacity.

## Query behavior

| Request | Expected result |
|---|---|
| Recognized airports with a fixture route | Matching projected flight fixtures |
| Recognized airports without a fixture route | A `no_fixture_route` result |
| Unknown flight airport or city | An `unsupported_airport` result |
| Recognized hotel city with fixtures | Matching hotel fixtures and calculated stay totals |
| City without hotel fixtures | An `unsupported_city` result with no hotels |
| Invalid dates or passenger/room counts | A validation error |

## Determinism

Stub-mode model behavior and MCP data are designed to be repeatable for interoperability tests.
Given the same supported prompt and fixture data, callers should receive equivalent tool selection
and domain results. Protocol identifiers and generated task metadata may still differ between
requests.

## Source files

The versioned catalog is stored alongside the MCP implementation:

- [Airport fixtures](../mcp-servers/src/travel_mcp/data/airports.json)
- [Flight fixtures](../mcp-servers/src/travel_mcp/data/flights.json)
- [Hotel fixtures](../mcp-servers/src/travel_mcp/data/hotels.json)
- [Catalog matching and calculation logic](../mcp-servers/src/travel_mcp/catalog.py)

## Extending the catalog

Contributions should:

- Use only data the contributor has the right to distribute.
- Keep simulated values clearly distinguishable from live inventory.
- Preserve stable identifiers where existing tests or clients depend on them.
- Add tests for aliases, validation, date handling, and price calculations.
- Update the coverage tables in this document when fixtures change.
