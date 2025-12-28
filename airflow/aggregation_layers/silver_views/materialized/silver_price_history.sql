SELECT
    f.id            AS flight_id,
    fp.found_at AS found_at,
    ss.site_aggregator,
    fp.currency,
    MIN(fp.amount) AS amount
FROM flight_prices fp
JOIN flights f ON f.id = fp.flight_id
JOIN search_sessions ss ON ss.id = fp.search_session_id
GROUP BY
    f.id,
    fp.found_at,
    ss.site_aggregator,
    fp.currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_flight_price_history
ON silver_price_history (
    flight_id,
    found_at,
    site_aggregator,
    currency
);