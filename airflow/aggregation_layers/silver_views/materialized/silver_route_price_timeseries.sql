SELECT
    request_id,
    route_id,
    route_type,
    found_at::date AS price_date,
    MIN(amount) AS min_price,
    currency
FROM silver_flight_prices_enriched
GROUP BY
    request_id,
    route_id,
    route_type,
    found_at::date,
    currency;


CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_route_price_ts
ON silver_route_price_timeseries (
    request_id,
    route_id,
    route_type,
    price_date,
    currency
);