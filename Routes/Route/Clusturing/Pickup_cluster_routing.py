
from Routes import home
from Models import db
from dateutil.parser import isoparse
from Models.Employee.Employees import Employees
from Models.Schedules.Employee_schedules import Employees_schedules
from Models.Route.Cluster.ManualClusteredPickupData import ManualClusteredData
from geopy.geocoders import Nominatim
from flask import request, jsonify
from sklearn.cluster import DBSCAN
import numpy as np
from geopy.distance import geodesic
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from functools import lru_cache

# Configuration Constants
OFFICE_COORDINATES = [17.441640, 78.381263]
AVERAGE_SPEED_KMPH = 10
PROXIMITY_THRESHOLD_KM = 2.5


# Estimate travel time based on straight-line distance
def estimate_travel_time_km(distance_km, speed_kmph=AVERAGE_SPEED_KMPH):
    hours = distance_km / speed_kmph
    return timedelta(hours=hours)

# Parse time
def parse_time(time_str):
    return datetime.strptime(time_str, "%H:%M:%S")


# Format time
def format_time(dt_obj):
    return dt_obj.strftime("%H:%M:%S")


def convert_manual_to_optimized_format(raw_data):
    result = []

    for time_group, clusters_dict in raw_data.items():
        cluster_list = []

        for idx, (cluster_key, cluster) in enumerate(clusters_dict.items(), start=1):
            # ✅ Use home_area directly instead of parsing address
            route_name = cluster.get("employeeList", [{}])[0].get('home_area', "UnknownRoute")

            cluster_list.append({
                "cluster_id": idx,
                "route_name": route_name,
                "pickup_sequence": cluster.get("employeeList", [])
            })

        result.append({
            "pickup_time_group": time_group,
            "destination": OFFICE_COORDINATES,
            "clusters": cluster_list
        })

    return result


# Cluster employees by proximity using Haversine (DBSCAN)
def cluster_employees_by_proximity(employees, threshold_km=PROXIMITY_THRESHOLD_KM, max_cluster_size=4):
    if not employees:
        return []

    coordinates = [emp['employee_coordinates'] for emp in employees]

    # Convert kilometers to radians for haversine
    kms_per_radian = 6371.0088
    epsilon = threshold_km / kms_per_radian
    radians_coords = np.radians(coordinates)

    db = DBSCAN(eps=epsilon, min_samples=1, algorithm='ball_tree', metric='haversine')
    labels = db.fit_predict(radians_coords)

    clusters = defaultdict(list)
    for label, emp in zip(labels, employees):
        clusters[label].append(emp)

    # Enforce cluster size limit
    final_clusters = []
    for cluster in clusters.values():
        final_clusters.extend(split_cluster_if_needed(cluster, max_size=max_cluster_size))

    return final_clusters


# Utility to split large clusters
def split_cluster_if_needed(cluster, max_size=4):
    return [cluster[i:i + max_size] for i in range(0, len(cluster), max_size)]


# Function to optimize group routes (updated for using address instead of coordinates)
def optimize_group_routes_from_dict(grouped_employees_dict):
    result = []

    for pickup_time_str, employees in grouped_employees_dict.items():
        pickup_group_time = parse_time(pickup_time_str)
        clusters = cluster_employees_by_proximity(employees)

        cluster_results = []

        for cluster_id, cluster in enumerate(clusters, start=1):
            sorted_cluster = sorted(
                cluster,
                key=lambda e: geodesic(e['employee_coordinates'], OFFICE_COORDINATES).km,
                reverse=True
            )

            total_route_time = timedelta()
            travel_times = []
            current_time = pickup_group_time

            for i in range(len(sorted_cluster)):
                origin = sorted_cluster[i]['employee_coordinates']
                dest = sorted_cluster[i + 1]['employee_coordinates'] if i < len(sorted_cluster) - 1 else OFFICE_COORDINATES

                dist = geodesic(origin, dest).km
                travel_time = estimate_travel_time_km(dist)

                travel_times.append(travel_time)
                total_route_time += travel_time

            current_time = pickup_group_time - total_route_time
            for idx, emp in enumerate(sorted_cluster):
                emp['pickup_sequence'] = idx + 1
                emp['calculated_pickup_time'] = format_time(current_time)

                if idx < len(travel_times):
                    current_time += travel_times[idx]

            # ✅ Use home_area directly for route name
            route_name = sorted_cluster[0].get('home_area', 'UnknownRoute')

            cluster_results.append({
                "cluster_id": cluster_id,
                "route_name": route_name,
                "pickup_sequence": sorted_cluster
            })

        result.append({
            "pickup_time_group": pickup_time_str,
            "destination": OFFICE_COORDINATES,
            "clusters": cluster_results
        })

    return result


# Flask endpoint (if using Flask)
@home.route('/get/pickup/clustered-routes', methods=['POST'])
def optimize_pickups():
    try:
        request_data = request.get_json()
        date_str = request_data.get('date', datetime.today().date().isoformat())

        try:
            selected_date = datetime.fromisoformat(date_str).date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD."}), 400

        # Fetch manual entry (if any)
        manual_entry = ManualClusteredData.query.filter_by(shift_date=selected_date).first()
        if manual_entry:
            transformed_data = convert_manual_to_optimized_format(manual_entry.data)
            return jsonify({"status": "success", "optimized_routes": transformed_data}), 200

        # Database query (if manual entry doesn't exist)
        data = db.session.query(Employees, Employees_schedules).join(
            Employees_schedules, Employees.employee_id == Employees_schedules.employee_id
        ).filter(Employees_schedules.shift_date == selected_date).all()

        grouped_pickup_schedules = {}
        for employees, schedules in data:
            if schedules and schedules.pickup_time:
                pickup_time = schedules.pickup_time
                if isinstance(pickup_time, str):
                    pickup_time = datetime.strptime(pickup_time, "%H:%M:%S").time()

                pickup_time_iso = pickup_time.isoformat()
                grouped_pickup_schedules.setdefault(pickup_time_iso, []).append({
                    'schedule_id': schedules.schedule_id,
                    'shift_date': schedules.shift_date.isoformat(),
                    'pickup_time': pickup_time_iso,
                    'drop_time': schedules.drop_time.isoformat() if schedules.drop_time else None,
                    'pickup_trip_status': schedules.pickup_trip_status,
                    'employee_id': employees.employee_id,
                    'employee_name': employees.employee_name,
                    'employee_address': employees.employee_address,
                    'employee_coordinates': [employees.latitude, employees.longitude],
                    'home_area': employees.home_area  # ✅ Added home_area field
                })

        # Call the optimized route calculation function
        optimized_data = optimize_group_routes_from_dict(grouped_pickup_schedules)

        return jsonify({
            "status": "success",
            "optimized_routes": optimized_data
        }), 200

    except Exception as e:
        logging.exception("Error optimizing pickup routes:")
        return jsonify({"status": "error", "message": str(e)}), 500




#update Routing clusters
@home.route('/get/pickup/updated/manual-clustered-routes', methods=['POST'])
def update_manual_cluster_data():
    try:
        request_data = request.get_json()
        clusters = request_data.get("clusters")
        date_str = request_data.get("date")

        if not clusters or not date_str:
            return jsonify({"status": "error", "message": "Missing 'clusters' or 'date' in request body"}), 400

        selected_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

        # Store or update the manual clusters
        existing = ManualClusteredData.query.filter_by(shift_date=selected_date).first()
        if existing:
            existing.data = clusters
        else:
            new_record = ManualClusteredData(shift_date=selected_date, data=clusters)
            db.session.add(new_record)

        # Also update employee_schedules table as before...
        for pickup_time_str, clusters_dict in clusters.items():
            for cluster_key, cluster in clusters_dict.items():
                pickup_sequence = cluster.get("employeeList", [])
                for order, emp_data in enumerate(pickup_sequence):
                    schedule_id = emp_data.get("schedule_id")
                    pickup_time_str = emp_data.get("calculated_pickup_time")

                    if not schedule_id or not pickup_time_str:
                        continue

                    try:
                        pickup_time = isoparse(pickup_time_str).time()
                    except Exception:
                        continue

                    schedule = Employees_schedules.query.filter_by(schedule_id=schedule_id).first()
                    if schedule:
                        schedule.pickup_time = pickup_time

        db.session.commit()
        return jsonify({"status": "success", "message": "Cluster data updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500



#Update Pickuptime and sequence
@home.route('/get/pickup/updated/manual-clustered-details/<employee_id>/<schedule_id>', methods=['PUT'])
def update_manual_cluster_details(employee_id, schedule_id):
    try:
        request_data = request.get_json()

        # Ensure the 'clusters' key is a dictionary
        clusters = request_data.get("clusters")
        if not isinstance(clusters, dict):
            return jsonify({"status": "error", "message": "'clusters' should be a dictionary"}), 400

        date_str = request_data.get("date")
        if not date_str:
            return jsonify({"status": "error", "message": "Missing 'date' in request body"}), 400

        selected_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

        # Store or update the manual clusters
        existing = ManualClusteredData.query.filter_by(shift_date=selected_date).first()
        if existing:
            existing.data = clusters
        else:
            new_record = ManualClusteredData(shift_date=selected_date, data=clusters)
            db.session.add(new_record)

        # Also update employee_schedules table as before...
        for pickup_time_str, clusters_dict in clusters.items():
            for cluster_key, cluster in clusters_dict.items():
                pickup_sequence = cluster.get("employeeList", [])
                for order, emp_data in enumerate(pickup_sequence):
                    schedule_id = emp_data.get("schedule_id")
                    pickup_time_str = emp_data.get("calculated_pickup_time")

                    if not schedule_id or not pickup_time_str:
                        continue

                    try:
                        pickup_time = isoparse(pickup_time_str).time()
                    except Exception:
                        continue

                    schedule = Employees_schedules.query.filter_by(schedule_id=schedule_id).first()
                    if schedule:
                        schedule.pickup_time = pickup_time

        db.session.commit()
        return jsonify({"status": "success", "message": "Cluster data updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500





#--------------------------------------------------------------------------------------------------------------
# Constants
# Constants













































