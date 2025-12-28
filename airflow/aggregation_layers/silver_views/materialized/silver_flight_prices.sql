SELECT
    f.id AS flight_id,
    f.route_id,
    r.departure,
    r.arrival,
    r.departure_date,
    f.airline_code,
    f.is_direct,
    f.stop_count,
    f.baggage_included,
    f.baggage_type,
    f.seats_left,

    fp.found_at AS found_at,
    ss.site_aggregator,
    fp.currency,

    MIN(fp.amount) AS best_price,
    MAX(fp.cashback_amount) AS cashback_amount,
    AVG(fp.amount) AS avg_price

FROM flight_prices fp
JOIN flights f ON f.id = fp.flight_id
JOIN search_sessions ss ON ss.id = fp.search_session_id
JOIN routes r ON r.id = f.route_id

GROUP BY
    f.id,
    f.route_id,
    r.departure,
    r.arrival,
    r.departure_date,
    f.airline_code,
    f.is_direct,
    f.stop_count,
    f.baggage_included,
    f.baggage_type,
    f.seats_left,
    fp.found_at,
    ss.site_aggregator,
    fp.currency;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_flight_price_snapshot
ON silver_flight_prices (
    flight_id,
    found_at,
    site_aggregator,
    currency
);