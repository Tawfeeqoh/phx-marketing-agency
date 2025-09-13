from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import requests
import os
import json

app = Flask(__name__)
CORS(app)

# GetResponse API configuration
GETRESPONSE_API_KEY = os.environ.get('GETRESPONSE_API_KEY')
GETRESPONSE_API_URL = 'https://api.getresponse.com/v3'

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/style.css')
def serve_css():
    return send_from_directory('.', 'style.css')

@app.route('/script.js')
def serve_js():
    return send_from_directory('.', 'script.js')

@app.route('/logo.png')
def serve_logo():
    return send_from_directory('.', 'logo.png')

@app.route('/submit-contact', methods=['POST'])
def submit_contact():
    try:
        # Get form data safely
        data = request.get_json(silent=True)
        if not data:
            return jsonify({
                'success': False,
                'error': 'Invalid request data'
            }), 400
            
        name = data.get('name', '').strip()
        email = data.get('email', '').strip()
        message = data.get('message', '').strip()
        
        # Validate required fields
        if not name or not email or not message:
            return jsonify({
                'success': False,
                'error': 'All fields are required'
            }), 400
        
        # Check if API key is available
        if not GETRESPONSE_API_KEY:
            return jsonify({
                'success': False,
                'error': 'GetResponse API key not configured'
            }), 500
        
        # Set up API headers
        headers = {
            'X-Auth-Token': f'api-key {GETRESPONSE_API_KEY}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Get campaigns
        campaigns_response = requests.get(
            f'{GETRESPONSE_API_URL}/campaigns',
            headers=headers,
            timeout=10
        )
        
        if campaigns_response.status_code != 200:
            return jsonify({
                'success': False,
                'error': 'Failed to connect to GetResponse'
            }), 500
        
        campaigns = campaigns_response.json()
        
        if not campaigns:
            return jsonify({
                'success': False,
                'error': 'No campaigns found in GetResponse account'
            }), 500
        
        # Use the first available campaign
        campaign_id = campaigns[0]['campaignId']
        
        # Add contact to GetResponse (without custom fields to avoid complications)
        contact_data = {
            'name': name,
            'email': email,
            'campaign': {
                'campaignId': campaign_id
            }
        }
        
        # Try to add the contact
        response = requests.post(
            f'{GETRESPONSE_API_URL}/contacts',
            headers=headers,
            json=contact_data,
            timeout=10
        )
        
        if response.status_code in [201, 202]:
            # Successfully created contact
            return jsonify({
                'success': True,
                'message': 'Thank you! Your message has been sent successfully and you\'ve been added to our mailing list.'
            })
        elif response.status_code == 409:
            # Contact already exists, that's okay
            return jsonify({
                'success': True,
                'message': 'Thank you! Your message has been received.'
            })
        else:
            # Log the error for debugging
            print(f"GetResponse API error: {response.status_code} - {response.text}")
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'Failed to add contact to mailing list. Please try again.'
            }), 500
            
    except requests.exceptions.Timeout:
        return jsonify({
            'success': False,
            'error': 'Request timed out. Please try again.'
        }), 500
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': 'Unable to connect to GetResponse. Please try again later.'
        }), 500
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'An unexpected error occurred. Please try again.'
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)