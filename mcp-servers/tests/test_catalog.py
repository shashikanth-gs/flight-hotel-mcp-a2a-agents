from __future__ import annotations

import unittest

from travel_mcp.catalog import list_airports, list_routes, search_flights, search_hotels


class CatalogTests(unittest.TestCase):
    def test_flight_dates_are_projected_from_template(self) -> None:
        result = search_flights("DEL", "BOM", "2030-01-15", adults=2)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["query"]["origin"], "DEL")
        self.assertTrue(result["flights"][0]["departure_at"].startswith("2030-01-15"))
        self.assertEqual(
            result["flights"][0]["price"]["total"],
            result["flights"][0]["price"]["per_adult"] * 2,
        )

    def test_city_names_resolve_to_airports(self) -> None:
        result = search_flights("Delhi", "Dubai", "2030-02-01")
        self.assertEqual(result["query"]["origin"], "DEL")
        self.assertEqual(result["query"]["destination"], "DXB")

    def test_overnight_flight_rolls_arrival_date(self) -> None:
        result = search_flights("BOM", "SIN", "2030-03-10")
        self.assertTrue(result["flights"][0]["arrival_at"].startswith("2030-03-11"))

    def test_hotel_total_uses_nights_and_rooms(self) -> None:
        result = search_hotels("Mumbai", "2030-04-01", "2030-04-04", guests=3, rooms=2)
        first = result["hotels"][0]
        self.assertEqual(first["nights"], 3)
        self.assertEqual(first["price"]["total"], first["price"]["nightly_per_room"] * 6)

    def test_invalid_date_range_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "after check_in"):
            search_hotels("Delhi", "2030-04-04", "2030-04-01")

    def test_catalog_has_india_and_international_coverage(self) -> None:
        self.assertGreaterEqual(len(list_airports("india")["airports"]), 8)
        self.assertGreaterEqual(len(list_airports("international")["airports"]), 8)
        self.assertGreaterEqual(len(list_routes()["routes"]), 10)


if __name__ == "__main__":
    unittest.main()
