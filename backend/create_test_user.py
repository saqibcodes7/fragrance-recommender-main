from flask import Flask
from models import db, User
import bcrypt

def create_test_user():
    # Create Flask app
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    with app.app_context():
        # Check if test user already exists
        if not User.query.filter_by(email='test@example.com').first():
            # Create test user
            password = 'Test123'.encode('utf-8')
            hashed_password = bcrypt.hashpw(password, bcrypt.gensalt())
            
            test_user = User(
                email='test@example.com',
                password=hashed_password
            )
            
            db.session.add(test_user)
            db.session.commit()
            print("Test user created successfully!")
        else:
            print("Test user already exists!")

if __name__ == '__main__':
    create_test_user() 