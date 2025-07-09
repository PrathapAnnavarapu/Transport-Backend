



from Routes import home
from Models import db
from Models.Route.Cluster.ManualClusteredDropData import ManualClusteredDropData
from dateutil.parser import isoparse
from Models.Employee.Employees import Employees
from Models.Schedules.Employee_schedules import Employees_schedules
from Models.Route.Cluster.ManualClusteredPickupData import ManualClusteredData
from datetime import datetime, timedelta
from geopy.distance import geodesic
from collections import defaultdict
import numpy as np
from sklearn.cluster import DBSCAN
import logging
from flask import jsonify, request

OFFICE_COORDINATES = [17.441640, 78.381263]  # Office coordinates (unchanged)
AVERAGE_SPEED_KMPH = 10  # Average speed (unchanged)
PROXIMITY_THRESHOLD_KM = 3.5  # Proximity threshold (unchanged)

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


# Function to convert raw data to optimized format for drop-off
def convert_manual_to_optimized_format_for_drop(raw_data):
    result = []

    for time_group, clusters_dict in raw_data.items():
        cluster_list = []

        for idx, (cluster_key, cluster) in enumerate(clusters_dict.items(), start=1):
            # Get the route name from the first employee's address in the cluster
            route_name = get_area_name_from_address_cached(
                cluster.get("employeeList", [{}])[0].get('employee_address', "Unknown Address")
            )

            # Append the cluster to the cluster list with the necessary data
            cluster_list.append({
                "cluster_id": idx,
                "route_name": route_name,  # Add route_name here
                "dropoff_sequence": cluster.get("employeeList", [])  # List of employees in the drop-off sequence
            })

        result.append({
            "dropoff_time_group": time_group,  # Drop-off time group (from raw data)
            "destination": OFFICE_COORDINATES,  # Office coordinates as destination
            "clusters": cluster_list  # List of clusters for this time group
        })

    return result


# Cluster employees by proximity using Haversine (DBSCAN)
def cluster_employees_by_proximity_for_drop(employees, threshold_km=PROXIMITY_THRESHOLD_KM, max_cluster_size=4):
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


# Function to get area name from address (address text as input)
def get_area_name_from_address_cached(address):
    if not address:
        return "UnknownRoute"

    parts = [p.strip() for p in address.split(",") if p.strip()]
    if len(parts) >= 3:
        return parts[2]  # Most likely area
    elif len(parts) >= 2:
        return parts[1]
    else:
        return parts[0]


# Function to optimize group drop routes (based on the employee's drop locations)
def optimize_group_drop_routes_from_dict(grouped_employees_dict):
    result = []

    for drop_time_str, employees in grouped_employees_dict.items():
        drop_group_time = parse_time(drop_time_str)  # Parse drop time for the group
        clusters = cluster_employees_by_proximity_for_drop(employees)  # Cluster employees by proximity for drops

        cluster_results = []

        for cluster_id, cluster in enumerate(clusters, start=1):
            # Sort employees: nearest to farthest (as per drop logic)
            sorted_cluster = sorted(
                cluster,
                key=lambda e: geodesic(e['employee_coordinates'], OFFICE_COORDINATES).km,
                reverse=False  # Nearest employees first for drop-off
            )

            # Calculate total route time based on proximity (no route distance)
            total_route_time = timedelta()
            travel_times = []
            current_time = drop_group_time  # Start with drop group time

            for i in range(len(sorted_cluster)):
                # Calculate travel time using straight-line distance between two consecutive employees
                origin = sorted_cluster[i]['employee_coordinates']
                dest = sorted_cluster[i + 1]['employee_coordinates'] if i < len(sorted_cluster) - 1 else OFFICE_COORDINATES

                dist = geodesic(origin, dest).km  # Straight-line distance between two points
                travel_time = estimate_travel_time_km(dist)  # Estimate travel time for the segment

                travel_times.append(travel_time)
                total_route_time += travel_time

            # Adjust for drop times based on the travel times
            current_time = drop_group_time - total_route_time  # Start with drop group time
            for idx, emp in enumerate(sorted_cluster):
                emp['drop_sequence'] = idx + 1  # Assign drop sequence
                emp['calculated_drop_time'] = format_time(current_time)  # Assign drop time

                # Update current time after this employee's drop-off
                if idx < len(travel_times):
                    current_time += travel_times[idx]

            # Get the route name from the address of the last employee (for drop)
            last_employee_address = sorted_cluster[-1]['employee_address']
            route_name = get_area_name_from_address_cached(last_employee_address)  # Get route name based on last employee's drop address

            cluster_results.append({
                "cluster_id": cluster_id,
                "route_name": route_name,
                "drop_sequence": sorted_cluster  # List of employees in the drop sequence
            })

        result.append({
            "drop_time_group": drop_time_str,  # Drop time group (in ISO format)
            "destination": OFFICE_COORDINATES,  # Office coordinates as destination
            "clusters": cluster_results  # List of clusters for this drop group
        })

    return result


# Flask endpoint for drop routes (similar to pickup endpoint)
@home.route('/get/drop/clustered-routes', methods=['POST'])
def optimize_drops():
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
            transformed_data = convert_manual_to_optimized_format_for_drop(manual_entry.data)
            return jsonify({"status": "success", "optimized_routes": transformed_data}), 200

        # Database query (if manual entry doesn't exist)
        data = db.session.query(Employees, Employees_schedules).join(
            Employees_schedules, Employees.employee_id == Employees_schedules.employee_id
        ).filter(Employees_schedules.shift_date == selected_date).all()

        grouped_drop_schedules = {}
        for employees, schedules in data:
            if schedules and schedules.drop_time:
                drop_time = schedules.drop_time
                if isinstance(drop_time, str):
                    drop_time = datetime.strptime(drop_time, "%H:%M:%S").time()

                drop_time_iso = drop_time.isoformat()
                grouped_drop_schedules.setdefault(drop_time_iso, []).append({
                    'schedule_id': schedules.schedule_id,
                    'shift_date': schedules.shift_date.isoformat(),
                    'pickup_time': schedules.pickup_time.isoformat() if schedules.pickup_time else None,
                    'drop_time': drop_time_iso,
                    'drop_trip_status': schedules.drop_trip_status,
                    'employee_id': employees.employee_id,
                    'employee_name': employees.employee_name,
                    'employee_address': employees.employee_address,
                    'employee_coordinates': [employees.latitude, employees.longitude]
                })

        # Call the optimized route calculation function
        optimized_data = optimize_group_drop_routes_from_dict(grouped_drop_schedules)

        return jsonify({
            "status": "success",
            "optimized_routes": optimized_data
        }), 200

    except Exception as e:
        logging.exception("Error optimizing drop routes:")
        return jsonify({"status": "error", "message": str(e)}), 500



@home.route('/get/drop/updated/manual-clustered-routes', methods=['POST'])
def update_manual_drop_cluster_data():
    try:
        request_data = request.get_json()
        clusters = request_data.get("clusters")
        date_str = request_data.get("date")

        if not clusters or not date_str:
            return jsonify({"status": "error", "message": "Missing 'clusters' or 'date'"}), 400

        selected_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

        existing = ManualClusteredDropData.query.filter_by(shift_date=selected_date).first()
        if existing:
            existing.data = clusters
        else:
            new_record = ManualClusteredDropData(shift_date=selected_date, data=clusters)
            db.session.add(new_record)

        for drop_time_str, clusters_dict in clusters.items():
            for cluster_key, cluster in clusters_dict.items():
                drop_sequence = cluster.get("employeeList", [])
                for order, emp_data in enumerate(drop_sequence):
                    schedule_id = emp_data.get("schedule_id")
                    drop_time_str = emp_data.get("calculated_drop_time")

                    if not schedule_id or not drop_time_str:
                        continue

                    try:
                        drop_time = isoparse(drop_time_str).time()
                    except Exception:
                        continue

                    schedule = Employees_schedules.query.filter_by(schedule_id=schedule_id).first()
                    if schedule:
                        schedule.drop_time = drop_time

        db.session.commit()
        return jsonify({"status": "success", "message": "Drop cluster data updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500



@home.route('/get/drop/updated/manual-clustered-details/<employee_id>/<schedule_id>', methods=['PUT'])
def update_manual_drop_cluster_details(employee_id, schedule_id):
    try:
        request_data = request.get_json()

        clusters = request_data.get("clusters")
        if not isinstance(clusters, dict):
            return jsonify({"status": "error", "message": "'clusters' should be a dictionary"}), 400

        date_str = request_data.get("date")
        if not date_str:
            return jsonify({"status": "error", "message": "Missing 'date' in request body"}), 400

        selected_date = datetime.strptime(date_str.split("T")[0], "%Y-%m-%d").date()

        # Store or update the manual clusters
        existing = ManualClusteredDropData.query.filter_by(shift_date=selected_date).first()
        if existing:
            existing.data = clusters
        else:
            new_record = ManualClusteredDropData(shift_date=selected_date, data=clusters)
            db.session.add(new_record)

        # Update the specific employee's drop_time
        for drop_time_group, cluster_dict in clusters.items():
            for cluster_key, cluster in cluster_dict.items():
                employee_list = cluster.get("employeeList", [])
                for emp_data in employee_list:
                    schedule_id_val = emp_data.get("schedule_id")
                    calculated_time = emp_data.get("calculated_drop_time")

                    if not schedule_id_val or not calculated_time:
                        continue

                    try:
                        drop_time = isoparse(calculated_time).time()
                    except Exception:
                        continue

                    # Only update the matching schedule_id and employee_id
                    if str(schedule_id_val) == str(schedule_id) and str(emp_data.get("employee_id")) == str(employee_id):
                        schedule = Employees_schedules.query.filter_by(schedule_id=schedule_id_val).first()
                        if schedule:
                            schedule.drop_time = drop_time

        db.session.commit()
        return jsonify({"status": "success", "message": "Drop cluster details updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500












