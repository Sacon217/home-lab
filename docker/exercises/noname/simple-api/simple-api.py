from flask import Flask, jsonify
app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return jsonify({'message': 'API is running'}), 200

@app.route('/home', methods=['GET'])
def home():
    return jsonify({'message': 'Welcome No Name Security!'}), 200

user_data={
    22: {'identification': "1-0021-1234", 'name': 'Sergio'},
    98: {'identification': "1-9954-5647", 'name': 'Zack'},
    12: {'identification': "1-9843-6433", 'name': 'Gabriel'},
    27: {'identification': "1-1022-5678" , 'name': 'Diana'}
}

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)