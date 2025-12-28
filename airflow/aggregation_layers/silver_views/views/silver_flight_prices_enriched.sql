SELECT
    fp.id                    AS flight_price_id,
    fp.found_at,
    fp.amount,
    fp.currency,
    ss.site_aggregator,

    f.id                     AS flight_id,
    f.airline_code,
    f.is_direct,
    f.stop_count,
    f.duration,
    f.baggage_included,
    f.baggage_type,
    f.seats_left,

    r.id                     AS route_id,
    r.route_type,
    r.departure,
    r.arrival,
    r.departure_date,

    req.id                   AS request_id,
    req.round_trip,
    req.adults

FROM flight_prices fp
JOIN flights f ON f.id = fp.flight_id
JOIN routes r ON r.id = f.route_id
JOIN requests req ON req.id = r.request_id
JOIN search_sessions ss ON ss.id = fp.search_session_id