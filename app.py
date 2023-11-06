from flask import Flask, request, jsonify
from flask_basicauth import BasicAuth
import psycopg2
import requests
import uuid
import os
from datetime import datetime

#DEBUG
#import logging
#logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)

# Basic Auth setup
app.config['BASIC_AUTH_USERNAME'] = os.getenv('APP_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('APP_PASSWORD')
basic_auth = BasicAuth(app)

# PostgreSQL database configuration
DATABASE_URI = os.getenv("DATABASE_URI")

# Cloudflare API credentials
CLOUDFLARE_API_KEY = os.getenv("CLOUDFLARE_API_KEY")
CLOUDFLARE_ZONE_ID = os.getenv("CLOUDFLARE_ZONE_ID")

# Function to initialize the database
def init_db():
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()

    # Create the ddns table if it doesn't exist
    cur.execute('''
        CREATE TABLE IF NOT EXISTS ddns (
            id SERIAL PRIMARY KEY,
            domain VARCHAR(255) UNIQUE NOT NULL,
            token VARCHAR(64) NOT NULL,
            ip VARCHAR(15),
            updated TIMESTAMP
        );
    ''')
    conn.commit()
    conn.close()

def update_timestamp_and_ip(domain, new_ip):
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()

    # Update the IP and timestamp for the given domain
    try:
        # First, fetch the current timestamp
        timestamp = datetime.now()

        # Update the "ip" and "updated" columns for the domain
        cur.execute("UPDATE ddns SET ip = %s, updated = %s WHERE domain = %s", (new_ip, timestamp, domain))
        conn.commit()
        conn.close()
    except Exception as e:
        conn.rollback()
        conn.close()
        raise e  # You can handle the exception as needed

# Function to generate a standard UUID
def generate_uuid():
    return str(uuid.uuid4())

# Function to add a new domain and generate a UUID
def add_domain_to_db(domain):
    # Check if the domain already exists
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()

    cur.execute("SELECT domain FROM ddns WHERE domain = %s", (domain,))
    result = cur.fetchone()

    if result:
        conn.close()
        return jsonify({"status": False, "message": "Domain already exists"}), 400

    # Generate a UUID string
    token = generate_uuid()

    # Insert the domain and token into the database
    try:
        cur.execute("INSERT INTO ddns (domain, token) VALUES (%s, %s)", (domain, token))
        conn.commit()
        conn.close()
        return jsonify({"status": True, "token": token}), 200
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({"status": False, "message": str(e)}), 500

def update_cloudflare_dns(domain, new_ip):
    success, record_identifier, record_content = get_zone_record_identifier(domain)
    if not success:
        return False, record_identifier
    if record_content == new_ip:
        return True, f"DNS record is already updated."

    # Define the API endpoint for updating the DNS record
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records/{record_identifier}"

    # Data for updating the DNS record
    update_data = {
        "content": new_ip,
        "name": domain,
        "proxied": False,
        "type": "A",
        "comment": "ddns-client"
    }

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"     
    }

    # Send the PUT request to update the DNS record
    response = requests.put(api_endpoint, json=update_data, headers=headers)
    print(response.text)
    if response.status_code == 200:
        return True, "DNS record updated successfully."
    else:
        return False, f"Failed to update DNS record. Status code: {response.status_code}, Response: {response.text}"

def get_zone_record_identifier(dns_record_name):
    # Define the API endpoint for fetching DNS records
    api_endpoint = f"https://api.cloudflare.com/client/v4/zones/{CLOUDFLARE_ZONE_ID}/dns_records"

    # Set the headers for the request
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {CLOUDFLARE_API_KEY}"     
    }

    # Send a GET request to fetch DNS records
    response = requests.get(api_endpoint, headers=headers)

    if response.status_code == 200:
        dns_records = response.json()["result"]
        for record in dns_records:
            if record["name"] == dns_record_name and record["type"] == "A":
                return True, record["id"], record["content"]
        return False, f'{{"response_code": {response.status_code}, "ddns_message": "Could not find matching DNS record at Cloudflare."}}', None
    else:
        return False, f'{{"response_code": {response.status_code}, "response_text": {response.text}}}', None

# Function to check token and domain in the database
def is_valid_token(token, domain):
    conn = psycopg2.connect(DATABASE_URI)
    cur = conn.cursor()
    cur.execute("SELECT token FROM ddns WHERE domain = %s", (domain,))
    result = cur.fetchone()
    conn.close()
    if result and result[0] == token:
        return True
    return False

# DDNS update endpoint
@app.route("/update", methods=["GET"])
def update_ddns():
    domain = request.args.get("domain")
    ip = request.args.get("ip")
    token = request.args.get("token")

    if not (domain and ip and token):
        return jsonify({"status": False, "message": "Invalid input received"}), 400
    if not is_valid_token(token, domain):
        return jsonify({"status": False, "message": "Authentication failed due to invalid token"}), 403
    success, message = update_cloudflare_dns(domain, ip)
    if success:
        update_timestamp_and_ip(domain, ip)
        return jsonify({"status": True, "message": message}), 200
    else:
        # Return the error message and a status code indicating the error
        return jsonify({"status": False, "message": message}), 500

# Route for adding a new domain
@app.route("/add_domain", methods=["GET"])
@basic_auth.required
def add_domain():
    domain = request.args.get("domain")
    if not domain:
        return jsonify({"status": False, "message": "Domain input is missing"}), 400

    response, status_code = add_domain_to_db(domain)
    return response, status_code

# Route to add list current domains with no secrets
@app.route("/list", methods=["GET"])
@basic_auth.required
def list_domains():
    return jsonify({"status": True, "message": "LIST OK"})

# Route to add list current domains with no secrets
@app.route("/delete_domain", methods=["GET"])
@basic_auth.required
def delete_domain():
    return jsonify({"status": True, "message": "DELETE OK"})

if __name__ == "__main__":
    init_db()  # Initialize the database
    #app.run(host="0.0.0.0", port=5000)
    app.run(host="0.0.0.0", port=5000, debug=True)

