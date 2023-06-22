import base64
import pickle

import rsa

from helpers.print_response import print_response


def login(req_sess):
    username = input('Username: ')
    password = input('Password: ').encode('utf8')
    two_factor = input('2FA Code: ')
    response_rsa = req_sess.post('https://steamcommunity.com/login/getrsakey/',
                                 data={'username': username})
    if response_rsa.status_code == 200:
        public_key = rsa.PublicKey(int(response_rsa.json()['publickey_mod'], 16),
                                   int(response_rsa.json()['publickey_exp'], 16))
        encrypted_password = base64.b64encode(rsa.encrypt(password, public_key))
        response_login = req_sess.post('https://steamcommunity.com/login/dologin/',
                                       data={'username': username, 'password': encrypted_password,
                                             'rsatimestamp': response_rsa.json()['timestamp'],
                                             'twofactorcode': two_factor})
        if response_login.status_code == 200:
            with open('../cookies', 'wb') as cookies_file:
                pickle.dump(req_sess.cookies, cookies_file)
            print('Login Successful')
        else:
            print('Login Failed')
            print_response(response_login)
    else:
        print('RSA Key Retrieval Failed')
        print_response(response_rsa)


def check_login(req_sess) -> bool:
    print('Checking Login Status...')
    response_logged_in = req_sess.get('https://steamcommunity.com/my', allow_redirects=False)
    if response_logged_in.status_code == 302:
        if 'login/home/?goto=%2Fmy' in response_logged_in.headers['Location']:
            print('Not Logged In')
            return False
        else:
            print('Logged In')
            return True
    else:
        print_response(response_logged_in)
        return False


def logout(req_sess) -> bool:
    print('Logging Out...')
    response_logout = req_sess.post('https://steamcommunity.com/login/logout/',
                                    data={'sessionid': req_sess.cookies.get('sessionid')})
    if response_logout.status_code == 200:
        if '/login/logout/' in response_logout.url:
            print('Logout was successful')
            return True
        else:
            print('Logout was unsuccessful, you might already be logged out.')
            return False
    else:
        print_response(response_logout)
        return False
