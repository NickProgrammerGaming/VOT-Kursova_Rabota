from flask import Flask, request, jsonify
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
import os

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
jwt = JWTManager(app)

NFS_PATH = "/mnt/nfs"

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    # Verify with Keycloak API (placeholder)
    if username == 'testuser' and password == 'password':
        token = create_access_token(identity=username)
        return jsonify(access_token=token)
    return jsonify({"msg": "Bad credentials"}), 401

@app.route('/file/upload', methods=['POST'])
@jwt_required()
def upload_file():
    file = request.files['file']
    file_path = os.path.join(NFS_PATH, file.filename)
    file.save(file_path)
    return jsonify({"msg": "File uploaded", "file": file.filename})

@app.route('/file/<file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    file_path = os.path.join(NFS_PATH, file_id)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            return f.read()
    return jsonify({"msg": "File not found"}), 404

@app.route('/file/<file_id>', methods=['PUT'])
@jwt_required()
def update_file(file_id):
    file_path = os.path.join(NFS_PATH, file_id)
    if os.path.exists(file_path):
        file = request.files['file']
        file.save(file_path)
        return jsonify({"msg": "File updated"})
    return jsonify({"msg": "File not found"}), 404

@app.route('/file/<file_id>', methods=['DELETE'])
@jwt_required()
def delete_file(file_id):
    file_path = os.path.join(NFS_PATH, file_id)
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({"msg": "File deleted"})
    return jsonify({"msg": "File not found"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
