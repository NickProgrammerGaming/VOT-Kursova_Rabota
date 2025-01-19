from flask import Flask, request, jsonify, send_file
from keycloak import KeycloakOpenID
import boto3
import os
from io import BytesIO
import config

app = Flask(__name__)

# Configure Keycloak
keycloak_openid = KeycloakOpenID(
    server_url=config.KEYCLOAK_SERVER_URL,
    client_id=config.KEYCLOAK_CLIENT_ID,
    realm_name=config.KEYCLOAK_REALM,
    client_secret_key=config.KEYCLOAK_CLIENT_SECRET
)

# Configure MinIO
s3 = boto3.client(
    's3',
    endpoint_url=config.MINIO_ENDPOINT,
    aws_access_key_id=config.MINIO_ACCESS_KEY,
    aws_secret_access_key=config.MINIO_SECRET_KEY
)
BUCKET_NAME = config.MINIO_BUCKET_NAME

# Ensure MinIO bucket exists
try:
    s3.head_bucket(Bucket=BUCKET_NAME)
except Exception:
    s3.create_bucket(Bucket=BUCKET_NAME)


# Verify JWT Token
def verify_token(auth_header):
    if not auth_header:
        return None, "Authorization header is missing."
    try:
        token = auth_header.split(" ")[1]  # Bearer <token>
        user_info = keycloak_openid.introspect(token)
        if not user_info.get("active"):
            return None, "Token is invalid or expired."
        return user_info, None
    except Exception as e:
        return None, f"Token verification failed: {str(e)}"


# Upload file
@app.route('/upload', methods=['POST'])
def upload_file():
    auth_header = request.headers.get('Authorization')
    user_info, error = verify_token(auth_header)
    if error:
        return jsonify({"error": error}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for uploading"}), 400

    try:
        s3.upload_fileobj(file, BUCKET_NAME, file.filename)
        return jsonify({"message": "File uploaded successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to upload file: {str(e)}"}), 500


# Download file
@app.route('/download/<filename>', methods=['GET'])
def download_file(filename):
    auth_header = request.headers.get('Authorization')
    user_info, error = verify_token(auth_header)
    if error:
        return jsonify({"error": error}), 401

    try:
        response = s3.get_object(Bucket=BUCKET_NAME, Key=filename)
        return send_file(BytesIO(response['Body'].read()), download_name=filename)
    except Exception as e:
        return jsonify({"error": f"Failed to download file: {str(e)}"}), 500


# Update file
@app.route('/update/<filename>', methods=['PUT'])
def update_file(filename):
    auth_header = request.headers.get('Authorization')
    user_info, error = verify_token(auth_header)
    if error:
        return jsonify({"error": error}), 401

    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected for updating"}), 400

    try:
        s3.upload_fileobj(file, BUCKET_NAME, filename)
        return jsonify({"message": "File updated successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to update file: {str(e)}"}), 500


# Delete file
@app.route('/delete/<filename>', methods=['DELETE'])
def delete_file(filename):
    auth_header = request.headers.get('Authorization')
    user_info, error = verify_token(auth_header)
    if error:
        return jsonify({"error": error}), 401

    try:
        s3.delete_object(Bucket=BUCKET_NAME, Key=filename)
        return jsonify({"message": "File deleted successfully!"}), 200
    except Exception as e:
        return jsonify({"error": f"Failed to delete file: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

