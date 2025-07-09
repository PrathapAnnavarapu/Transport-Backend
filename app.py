from flask import Flask
from flask_cors import CORS
import os
from Models import db
from Routes import home
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost:3306/transport_project'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', '123456789')

    db.init_app(app)
    jwt = JWTManager(app)
    migrate = Migrate(app, db)

    # Enable CORS for all routes
    CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}})

    with app.app_context():
        db.create_all()  # Create all tables based on the models defined
        db.session.commit()

    app.register_blueprint(home, url_prefix='/api')
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5001)