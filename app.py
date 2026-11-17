from flask import Flask, jsonify, request
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

LOGIN_URL = "https://customercenter.phibo.com/Account/Login?ReturnUrl=%2f"
CC_MANAGER_URL = "https://customercenter.phibo.com/CCManager"
TICKETING_URL = "https://customercenter.phibo.com/NewHelpdesk"

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
    
    # Comprovar si el login ha estat correcte (si ens ha portat a la pàgina principal)
    if "Account/Login" in login_res.url:
        return jsonify({'success': False, 'message': 'Usuari o contrasenya incorrectes'}), 401
        
    # Guardem les galetes de sessió per a aquest usuari (en producció es pot gestionar amb un diccionari o token)
    app.config['USER_SESSION'] = session
    return jsonify({'success': True, 'message': 'Login correcte'})

@app.route('/api/ccmanager', methods=['GET'])
def get_ccmanager():
    session = app.config.get('USER_SESSION')
    if not session:
        return jsonify({'error': 'No autoritzat'}), 401
        
    res = session.get(CC_MANAGER_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    # Aquí pots extreure les taules o dades concretes de Programacion.aspx
    # Per exemple, recollir files de taules o missatges clau:
    content = soup.find('div', {'id': 'frm_base'}) or soup.find('div', {'class': 'body-content'})
    
    return jsonify({'html': str(content)})

@app.route('/api/ticketing', methods=['GET'])
def get_ticketing():
    session = app.config.get('USER_SESSION')
    if not session:
        return jsonify({'error': 'No autoritzat'}), 401
        
    res = session.get(TICKETING_URL)
    soup = BeautifulSoup(res.text, 'html.parser')
    content = soup.find('div', {'class': 'body-content'})
    
    return jsonify({'html': str(content)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)