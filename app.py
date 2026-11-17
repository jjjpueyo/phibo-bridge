from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import os

app = Flask(__name__, static_folder='.')
CORS(app)

LOGIN_URL = "https://customercenter.phibo.com/Account/Login?ReturnUrl=%2f"
CC_MANAGER_URL = "https://customercenter.phibo.com/CCManager"
TICKETING_URL = "https://customercenter.phibo.com/NewHelpdesk"

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    session = requests.Session()
    
    # 1. Obtenir el token de verificació de la pàgina de login
    res = session.get(LOGIN_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    token_input = soup.find('input', {'name': '__RequestVerificationToken'})
    token = token_input['value'] if token_input else ''
    
    # 2. Fer el POST d'inici de sessió
    payload = {
        '__RequestVerificationToken': token,
        'UserName': username,
        'Password': password,
        'RememberMe': 'true'
    }
    headers = {'Referer': LOGIN_URL}
    login_res = session.post(LOGIN_URL, data=payload, headers=headers, allow_redirects=True)
    
    # Comprovar si el login ha estat correcte
    if "Account/Login" in login_res.url:
        return jsonify({'success': False, 'message': 'Usuari o contrasenya incorrectes'}), 401
        
    app.config['USER_SESSION'] = session
    return jsonify({'success': True, 'message': 'Login correcte'})

@app.route('/api/ccmanager', methods=['GET'])
def get_ccmanager():
    session = app.config.get('USER_SESSION')
    if not session:
        return jsonify({'error': 'No autoritzat'}), 401
        
    res = session.get(CC_MANAGER_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = soup.find('form', {'id': 'frm_base'}) or soup.find('div', {'class': 'body-content'})
    
    return jsonify({'html': str(content) if content else res.text})

@app.route('/api/ticketing', methods=['GET'])
def get_ticketing():
    session = app.config.get('USER_SESSION')
    if not session:
        return jsonify({'error': 'No autoritzat'}), 401
        
    res = session.get(TICKETING_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = soup.find('div', {'class': 'body-content'})
    
    return jsonify({'html': str(content) if content else res.text})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
