from flask import Flask, jsonify, request
import secrets
import os
import sqlite3

app = Flask(__name__)

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

def init_db():
    conn = sqlite3.connect('demo.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS products
                 (id INTEGER PRIMARY KEY, name TEXT, price REAL, additional_info TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, user TEXT, password TEXT)''')
    

    c.execute("DELETE FROM products")
    c.execute("DELETE FROM users")
    
    c.execute("INSERT INTO products VALUES (1, 'UGREEN NAS', 349.99, 'NAS DXP2800 2-Bay')")
    c.execute("INSERT INTO products VALUES (2, 'UNMANAGED SWITCH', 59.99, 'TP-Link TL-SG105S-M2')")
    c.execute("INSERT INTO products VALUES (3, '2x32GB STICKS OF RAM', 10000.50, 'GSKILL DDR5 2x32GB ECC RAM')")
    c.execute("INSERT INTO users VALUES (1, 'sacon28', '6OzP!CX#Ap')")
    c.execute("INSERT INTO users VALUES (2, 'admin', '0BE&Xdt^T77orMrgwsUs2O4l%')")

    conn.commit()
    conn.close()

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'API is running'}), 200

@app.route('/home', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome No Name Security!'}), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    return jsonify({
        'total_users': len(user_data),
        'users': user_data
    }), 200

@app.route('/user/<user_id>/settings', methods=['GET'])
def get_user_settings(user_id):
    try:
        user_id_int = int(user_id)
    except ValueError:
        return jsonify({'error': 'Invalid user ID format'}), 400
    
    if not 0 <= user_id_int <= 100:
        return jsonify({'error': 'User ID must be between 0 and 100'}), 400
    
    user = user_data.get(user_id_int)
    if user:
        return jsonify({
            'user_id': str(user_id_int),
            'settings': {
                'email': user['email'],
                'ssn': user['ssn'],
                'credit_card': user['credit_card'],
                'api_key': user['api_key']
            }
        }), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/db/restart', methods=['GET'])
def restart_db():
    init_db()
    return jsonify({'message': 'Database restarted'}), 200

@app.route('/db/search', methods=['GET'])
def vulnerable_search():
    search_query = request.args.get('query', '')
    
    conn = sqlite3.connect('demo.db')
    c = conn.cursor()
    sql = f"SELECT id, name, price, additional_info FROM products WHERE name LIKE '%{search_query}%'"
    
    try:
        c.execute(sql)
        results = c.fetchall()
        conn.close()
        
        return jsonify({
            'results': [{'id': r[0], 'name': r[1], 'price': r[2], 'info': r[3]} for r in results]
        }), 200
    except Exception as e:
        conn.close()
        return jsonify({'error': str(e), 'sql': sql}), 404

@app.route('/login', methods=['POST'])
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
    port_number = int(os.getenv('PORT_NUMBER', '5000'))
    init_db()
    print(f"Starting Flask on port {port_number}")
    app.run(host='0.0.0.0', port=port_number, debug=True)