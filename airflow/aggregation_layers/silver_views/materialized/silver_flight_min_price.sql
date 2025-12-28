SELECT
    flight_id,
    MIN(amount) AS min_price,
    currency
FROM silver_flight_prices_enriched
GROUP BY flight_id, currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_flight_min_price
ON silver_flight_min_price (flight_id, currency);