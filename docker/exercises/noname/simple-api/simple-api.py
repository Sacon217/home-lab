from flask import Flask, jsonify, request
import hashlib
import secrets
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'API is running'}), 200

@app.route('/home', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome No Name Security!'}), 200

user_data={
    22: {
        'identification': "1-0021-1234", 
        'name': 'Sergio',
        'email': 'sergio@company.com',
        'password': 'SuperSecret123!',
        'ssn': '123-45-6789',
        'credit_card': '4532-1234-5678-9010',
        'api_key': 'sk_live_51234567890abcdef'
    },
    98: {
        'identification': "1-9954-5647", 
        'name': 'Zack',
        'email': 'zack@company.com',
        'password': 'Password123',
        'ssn': '987-65-4321',
        'credit_card': '5425-2334-3010-9876',
        'api_key': 'sk_live_98765432109876543'
    },
    12: {
        'identification': "1-9843-6433", 
        'name': 'Gabriel',
        'email': 'gabriel@company.com',
        'password': 'MyP@ssw0rd',
        'ssn': '456-78-9012',
        'credit_card': '3782-822463-10005',
        'api_key': 'sk_live_abcdefghijklmnop'
    },
    27: {
        'identification': "1-1022-5678", 
        'name': 'Diana',
        'email': 'diana@company.com',
        'password': 'Diana2024!',
        'ssn': '789-01-2345',
        'credit_card': '6011-1111-1111-1117',
        'api_key': 'sk_live_qrstuvwxyz123456'
    }
}

active_sessions = {}

@app.route('/users', methods=['GET'])
def get_all_users():
    all_users = {str(user_id): user_data[user_id] for user_id in user_data}
    return jsonify({
        'total_users': len(user_data),
        'users': all_users
    }), 200

@app.route('/users/<user_id>', methods=['GET'])
def get_user(user_id):
    user = user_data.get(int(user_id), None)
    if user:
        return jsonify({'user': user}), 200
    else:
        return jsonify({'message': 'User not found'}), 404

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    for user_id, user in user_data.items():
        if user['email'] == email and user['password'] == password:
            session_token = secrets.token_hex(32)
            active_sessions[session_token] = {
                'user_id': user_id,
                'email': email,
                'name': user['name']
            }
            
            return jsonify({
                'success': True,
                'message': 'Login successful',
                'session_token': session_token,
                'user': {
                    'name': user['name'],
                    'email': user['email']
                },
            }), 200
    
    return jsonify({
        'success': False,
        'message': 'Invalid credentials'
    }), 401

if __name__ == '__main__':
    port_number = os.getenv('PORT_NUMBER', 5000)
    app.run(host='0.0.0.0', port=port_number, debug=True)