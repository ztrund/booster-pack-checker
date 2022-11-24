import base64
import os.path
import requests
import rsa


def menu():  # Temporary cli menu until I build gui
    while True:
        print('1.Login to Steam (Increases Update Rate Significantly)')
        print('2.Update Games List and Booster Pack Prices')
        print('3.Update Trading Card Prices')
        print('4.Exit')
        choice = input('Enter Selection: ')
        match choice:
            case '1':
                login()
            case '2':
                update_boosters()
            case '3':
                update_cards()
            case '4':
                print('Exiting Program...')
                break
            case _:
                print('INVALID SELECTION')


def login():  # Add Error Catching
    if os.path.exists('cookie.txt'):
        print('It looks like you are already logged in.')
        if input('Press 1 if you want to log out and log in again: ') != '1':
            return True
        os.remove('cookie.txt')
    username = input('Username: ')
    password = input('Password: ').encode('utf8')
    two_factor = input('2FA Code: ')
    response_rsa = requests.post('https://steamcommunity.com/login/getrsakey/',
                                 data={'username': username})
    public_key = rsa.PublicKey(int(response_rsa.json()['publickey_mod'], 16),
                               int(response_rsa.json()['publickey_exp'], 16))
    encrypted_password = base64.b64encode(rsa.encrypt(password, public_key))
    response_login = requests.post('https://steamcommunity.com/login/dologin/',
                                   data={'username': username, 'password': encrypted_password,
                                         'rsatimestamp': response_rsa.json()['timestamp'], 'twofactorcode': two_factor})
    with open('cookie.txt', 'w') as cookie_file:
        cookie_file.write(response_login.cookies['steamLoginSecure'])


def update_boosters():
    print('Update Boosters')


def update_cards():
    print('Update Trading Cards')


if __name__ == '__main__':
    menu()
