from api.airline_console.airline_engine import get_city_by_airport_code
from flask import Flask, Blueprint, request, jsonify
from api.reader import get_session_and_engine
from api.airline_service.threat_service import (
    get_incident_feed,
    get_bookings,
    get_status_distribution,
    get_escalation_rate,
    get_dashboard_map_data,
    process_city_disruption,
)

api = Blueprint("airline_api", __name__)


# DASHBOARD ENDPOINTS
@api.route("/dashboard/summary", methods=["GET"])
def dashboard_summary():
    session, _ = get_session_and_engine()
    try:
        return jsonify(get_incident_feed(session)), 200
    finally:
        session.close()


@api.route("/dashboard/map", methods=["GET"])
def dashboard_map():
    session, _ = get_session_and_engine()
    try:
        return jsonify(get_dashboard_map_data(session)), 200
    finally:
        session.close()


@api.route("/bookings", methods=["GET"])
def bookings():
    flight_id = request.args.get("flight")
    city_name = request.args.get("city")
    session, _ = get_session_and_engine()
    try:
        return jsonify(get_bookings(session, flight_id=flight_id, city=city_name)), 200
    finally:
        session.close()


@api.route("/analytics/status-distribution", methods=["GET"])
def analytics_status():
    session, _ = get_session_and_engine()
    try:
        return jsonify(get_status_distribution(session)), 200
    finally:
        session.close()


@api.route("/analytics/escalation-rate", methods=["GET"])
def analytics_escalation():
    session, _ = get_session_and_engine()
    try:
        return jsonify(get_escalation_rate(session)), 200
    finally:
        session.close()


@api.route("/disruption/city", methods=["POST"])
def city_disruption():
    data = request.json or {}

    airport_code = data.get("airport_code")
    disruption_type = data.get("type")
    alternate_airport = data.get("alternate_airport")
    severity = data.get("severity")[0]

    if not airport_code or not disruption_type:
        return jsonify({"error": "airport_code and type are required"}), 400

    session, _ = get_session_and_engine()
    try:
        print(data)
        city_name = get_city_by_airport_code(session, airport_code)
        print("city_name::", city_name)
        result = process_city_disruption(
            city=city_name,
            disruption_type=disruption_type,
            alternate_airport=alternate_airport,
            severity=severity,
        )
        return jsonify(result), 200

    except ValueError as ve:
        return jsonify({"error": str(ve)}), 404
    except Exception as ex:
        print(ex)
        return jsonify({"error": "Disruption handling failed"}), 500
    finally:
        session.close()


#====app creation====
def create_app():
    app = Flask(__name__)
    app.register_blueprint(api)
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
