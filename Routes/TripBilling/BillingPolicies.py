from flask import Blueprint, request, jsonify
from Models import db
from Models.TripBilling.BillingPolicies import BillingPolicy, Zone

from Routes import home

# CREATE
# Helper functions for type conversion
def to_float(value, default=0.0):
    try:
        return float(value) if value != '' else default
    except (TypeError, ValueError):
        return default  # return default if the conversion fails

def to_int(value, default=0):
    try:
        return int(value) if value != '' else default
    except (TypeError, ValueError):
        return default  # return default if the conversion fails

@home.route('/add/billing-policies', methods=['POST'])
def create_billing_policy():
    data = request.get_json()

    # Use helper functions to sanitize input
    policy = BillingPolicy(
        billing_mode=data.get('billing_mode'),
        base_fare=to_float(data.get('base_fare', 0.0)),
        rate_per_km=to_float(data.get('rate_per_km', 0.0)),
        rate_per_min=to_float(data.get('rate_per_min', 0.0)),
        night_surcharge_multiplier=to_float(data.get('night_surcharge_multiplier', 1.0)),
        plan_name=data.get('plan_name') or None,
        monthly_fee=to_float(data.get('monthly_fee', 0.0)),
        included_rides=to_int(data.get('included_rides', 0)),
        extra_ride_price=to_float(data.get('extra_ride_price', 0.0)),
        is_active=data.get('is_active', True)
    )

    # Handle zones data
    zones_data = data.get('zones', [])
    for zone in zones_data:
        new_zone = Zone(
            zone_name=zone.get('zone_name'),
            distance_min=to_float(zone.get('distance_min', 0.0)),
            distance_max=to_float(zone.get('distance_max', 0.0)),
            fixed_price=to_float(zone.get('fixed_price', 0.0))
        )
        policy.zones.append(new_zone)

    # Commit to the database
    db.session.add(policy)
    db.session.commit()

    # Return response with the created policy ID
    return jsonify({"message": "Billing policy created", "id": policy.id}), 201





# READ
@home.route('/get/billing-policies', methods=['GET'])
def get_billing_policies():
    policies = BillingPolicy.query.all()
    result = []
    for p in policies:
        result.append({
            "id": p.id,
            "billing_mode": p.billing_mode,
            "base_fare": p.base_fare,
            "rate_per_km": p.rate_per_km,
            "rate_per_min": p.rate_per_min,
            "night_surcharge_multiplier": p.night_surcharge_multiplier,
            "plan_name": p.plan_name,
            "monthly_fee": p.monthly_fee,
            "included_rides": p.included_rides,
            "extra_ride_price": p.extra_ride_price,
            "is_active": p.is_active,
            "created_at": p.created_at,
            "zones": [
                {
                    "id": z.id,
                    "zone_name": z.zone_name,
                    "distance_min": z.distance_min,
                    "distance_max": z.distance_max,
                    "fixed_price": z.fixed_price
                } for z in p.zones
            ]
        })
    return jsonify(result), 200


@home.route('/get/billing-policies/names', methods=['GET'])
def get_billing_policies_with_names():
    policies = BillingPolicy.query.all()
    result = []
    for p in policies:
        result.append({
            "id": p.id,
            "billing_mode": p.billing_mode,
        })
    return jsonify(result), 200

# UPDATE
@home.route('/update/billing-policies/<int:id>', methods=['PUT'])
def update_billing_policy(id):
    policy = BillingPolicy.query.get_or_404(id)
    data = request.get_json()

    policy.billing_mode = data.get('billing_mode', policy.billing_mode)
    policy.base_fare = data.get('base_fare', policy.base_fare)
    policy.rate_per_km = data.get('rate_per_km', policy.rate_per_km)
    policy.rate_per_min = data.get('rate_per_min', policy.rate_per_min)
    policy.night_surcharge_multiplier = data.get('night_surcharge_multiplier', policy.night_surcharge_multiplier)
    policy.plan_name = data.get('plan_name', policy.plan_name)
    policy.monthly_fee = data.get('monthly_fee', policy.monthly_fee)
    policy.included_rides = data.get('included_rides', policy.included_rides)
    policy.extra_ride_price = data.get('extra_ride_price', policy.extra_ride_price)
    policy.is_active = data.get('is_active', policy.is_active)

    # Update zones
    db.session.query(Zone).filter_by(billing_policy_id=id).delete()
    zones_data = data.get('zones', [])
    for zone in zones_data:
        new_zone = Zone(
            zone_name=zone.get('zone_name'),
            distance_min=zone.get('distance_min', 0.0),
            distance_max=zone.get('distance_max', 0.0),
            fixed_price=zone.get('fixed_price', 0.0),
            billing_policy_id=policy.id
        )
        db.session.add(new_zone)

    db.session.commit()
    return jsonify({"message": "Billing policy updated"}), 200

# DELETE
@home.route('/delete/billing-policies/<int:id>', methods=['DELETE'])
def delete_billing_policy(id):
    policy = BillingPolicy.query.get_or_404(id)
    db.session.delete(policy)
    db.session.commit()
    return jsonify({"message": "Billing policy deleted"}), 200
