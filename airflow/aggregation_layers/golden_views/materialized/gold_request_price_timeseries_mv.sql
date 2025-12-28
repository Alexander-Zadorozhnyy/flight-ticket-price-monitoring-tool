SELECT
    request_id,
    route_type,
    price_date,
    MIN(min_price) AS min_price,
    currency
FROM silver_route_price_timeseries
GROUP BY
    request_id,
    route_type,
    price_date,
    currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_gold_price_ts
ON gold_request_price_timeseries_mv (request_id, route_type, price_date, currency);