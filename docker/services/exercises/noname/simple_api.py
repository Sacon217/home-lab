from flask import Flask, request, jsonify


app = Flask(__name__)


@app.route('/')
def home():
    response_name = {"message": "Welcome No Name Security!"}
    return jsonify(response_name), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 