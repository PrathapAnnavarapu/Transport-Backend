from flask import Blueprint, request, jsonify
from Models import db
try:
    from Models.Locations.Locations import Locations
except ImportError:
    # Create Locations model if it doesn't exist
    class Locations(db.Model):
        __tablename__ = 'locations'
        
        id = db.Column(db.Integer, primary_key=True)
        location_name = db.Column(db.String(100), nullable=False, unique=True)
        location_address = db.Column(db.String(255))
        latitude = db.Column(db.Float, nullable=False)
        longitude = db.Column(db.Float, nullable=False)
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=db.func.now())
        
        def to_dict(self):
            return {
                'id': self.id,
                'location_name': self.location_name,
                'location_address': self.location_address,
                'latitude': self.latitude,
                'longitude': self.longitude,
                'is_active': self.is_active
            }

locations_bp = Blueprint('locations', __name__)


@locations_bp.route('/api/locations/all', methods=['GET'])
def get_all_locations():
    """Get all active locations"""
    try:
        locations = Locations.query.filter_by(is_active=True).all()
        return jsonify({
            'success': True,
            'data': [loc.to_dict() for loc in locations]
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@locations_bp.route('/api/locations/<int:location_id>', methods=['GET'])
def get_location(location_id):
    """Get specific location by ID"""
    try:
        location = Locations.query.get(location_id)
        if not location:
            return jsonify({'success': False, 'message': 'Location not found'}), 404
        
        return jsonify({
            'success': True,
            'data': location.to_dict()
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@locations_bp.route('/api/locations/add', methods=['POST'])
def add_location():
    """Add new location"""
    try:
        data = request.get_json()
        
        location = Locations(
            location_name=data['location_name'],
            location_address=data.get('location_address'),
            latitude=data['latitude'],
            longitude=data['longitude'],
            is_active=data.get('is_active', True)
        )
        
        db.session.add(location)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location added successfully',
            'data': location.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@locations_bp.route('/api/locations/update/<int:location_id>', methods=['PUT'])
def update_location(location_id):
    """Update location"""
    try:
        location = Locations.query.get(location_id)
        if not location:
            return jsonify({'success': False, 'message': 'Location not found'}), 404
        
        data = request.get_json()
        
        if 'location_name' in data:
            location.location_name = data['location_name']
        if 'location_address' in data:
            location.location_address = data['location_address']
        if 'latitude' in data:
            location.latitude = data['latitude']
        if 'longitude' in data:
            location.longitude = data['longitude']
        if 'is_active' in data:
            location.is_active = data['is_active']
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location updated successfully',
            'data': location.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@locations_bp.route('/api/locations/delete/<int:location_id>', methods=['DELETE'])
def delete_location(location_id):
    """Soft delete location (set is_active=False)"""
    try:
        location = Locations.query.get(location_id)
        if not location:
            return jsonify({'success': False, 'message': 'Location not found'}), 404
        
        location.is_active = False
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Location deactivated successfully'
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
