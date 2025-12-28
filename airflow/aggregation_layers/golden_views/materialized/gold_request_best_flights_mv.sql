SELECT DISTINCT ON (request_id, route_type)
    request_id,
    route_type,
    flight_id,
    amount AS best_price,
    currency,
    site_aggregator,
    found_at
FROM silver_flight_prices_enriched
ORDER BY request_id, route_type, amount, found_at DESC;

CREATE UNIQUE INDEX IF NOT EXISTS ux_gold_best_flights
ON gold_request_best_flights_mv (request_id, route_type);