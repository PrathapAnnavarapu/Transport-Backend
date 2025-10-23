from flask import jsonify, request
from Models import db
from Models.SPOC.SpocList import Spocs
from Routes import home

@home.route('/add/new/spoc', methods=['POST'])
def get_spocs():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'req data is empty'}), 400

    new_spoc = Spocs(spocData=data)

    try:
        db.session.add(new_spoc)
        db.session.commit()
        return jsonify({'message': 'SPOC added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@home.route('/get/spocs/all', methods=['GET'])
def get_spocs_all():
    if request.method == 'OPTIONS':
        return '', 200

    data = Spocs.query.all()
    spocs_list = [
        {
            'id': e.id,
            'spoc_name': e.spocData.get('employee_name') if e.spocData else None,
            'spoc_id': e.spocData.get('employee_id') if e.spocData else None,
            'spoc_mobile_no': e.spocData.get('employee_mobile_no') if e.spocData else None,
            'gender': e.spocData.get('gender') if e.spocData else None,
            'spoc_email': e.spocData.get('employee_email') if e.spocData else None,
            'role': e.spocData.get('role') if e.spocData else None,
            'process': e.spocData.get('process') if e.spocData else None,
            'active_status': e.spocData.get('active_status') if e.spocData else None,
        }
        for e in data
    ]

    return jsonify(spocs_list), 200

