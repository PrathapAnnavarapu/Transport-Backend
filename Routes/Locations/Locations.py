

from flask import jsonify, request
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from geopy.geocoders import Nominatim
import pandas as pd
import json
from werkzeug.utils import secure_filename
import os
from Models import db
from Models.Locations.Location import Locations
from Routes import home



@home.route('/add/new/location', methods=['POST'])
def add_location():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request data is empty'}), 400

    # required_fields = ['locationName', 'locationCode', 'address', 'city', 'state', 'country']
    # for field in required_fields:
    #     if not data.get(field):
    #         return jsonify({'error': f'{field} is required'}), 400

    try:
        new_location = Locations(
            location_name=data['locationName'],
            location_code=data['locationCode'],
            address=data['address'],
            city=data['city'],
            state=data['state'],
            country=data['country'],
            is_active=data.get('is_active', True)
        )

        db.session.add(new_location)
        db.session.commit()
        return jsonify({'message': 'Location added successfully', 'id': new_location.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500





@home.route('/locations/all', methods=['GET', 'OPTIONS'])
def get_locations():
    if request.method == 'OPTIONS':
        return '', 200

    data = Locations.query.all()
    locations_list = [
        {
            'id': loc.id,
            'location_name': loc.location_name,
            'location_code': loc.location_code,
            'address': loc.address,
            'city': loc.city,
            'state': loc.state,
            'country': loc.country,
            'is_active': loc.is_active
        }
        for loc in data
    ]
    return jsonify(locations_list), 200



@home.route('/locations/update/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Request data is empty'}), 400

    location = Locations.query.get(location_id)
    if not location:
        return jsonify({'error': 'Location not found'}), 404

    try:
        # Update only provided fields
        location.location_name = data.get('location_name', location.location_name)
        location.location_code = data.get('location_code', location.location_code)
        location.address = data.get('address', location.address)
        location.city = data.get('city', location.city)
        location.state = data.get('state', location.state)
        location.country = data.get('country', location.country)
        location.is_active = data.get('is_active', location.is_active)

        db.session.commit()
        return jsonify({'message': 'Location updated successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500



@home.route('/locations/delete/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    location = Locations.query.get(location_id)

    if not location:
        return jsonify({'error': 'Location not found'}), 404

    try:
        db.session.delete(location)
        db.session.commit()
        return jsonify({'message': 'Location deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
