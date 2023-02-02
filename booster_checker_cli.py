import base64
import pickle
import sqlite3
import time

import requests
import rsa


def menu():  # Temporary cli menu until I build gui
    while True:
        print('1.Login to Steam (Increases Update Rate Significantly)')
        print('2.Update Games List and Booster Pack Prices')
        print('3.Update Trading Card Prices')
        print('4.Check Login Status')
        print('5.Logout of Steam')
        print('0.Exit')
        choice = input('Enter Selection: ')
        match choice:
            case '1':
                login()
            case '2':
                update_boosters()
            case '3':
                update_cards()
            case '4':
                check_login()
            case '5':
                logout()
            case '0':
                print('Exiting Program...')
                break
            case _:
                print('INVALID SELECTION')


def login():  # Add Error Catching
    username = input('Username: ')
    password = input('Password: ').encode('utf8')
    two_factor = input('2FA Code: ')
    response_rsa = req_sess.post('https://steamcommunity.com/login/getrsakey/',
                                 data={'username': username})
    public_key = rsa.PublicKey(int(response_rsa.json()['publickey_mod'], 16),
                               int(response_rsa.json()['publickey_exp'], 16))
    encrypted_password = base64.b64encode(rsa.encrypt(password, public_key))
    response_login = req_sess.post('https://steamcommunity.com/login/dologin/',
                                   data={'username': username, 'password': encrypted_password,
                                         'rsatimestamp': response_rsa.json()['timestamp'], 'twofactorcode': two_factor})
    with open('cookies', 'wb') as f:
        pickle.dump(req_sess.cookies, f)
    print(response_login.status_code)
    print(response_login.headers)
    print(response_login.reason)
    print(response_login.cookies)
    print(response_login.raw)
    print(response_login.encoding)
    print(response_login.elapsed)


def update_boosters():
    if not check_login():
        if input(
                'It looks like you are not logged in, the update rate will be significantly slower (Press 1 if you wish'
                'to continue without logging in):') != 1:
            return
    print('Updating Boosters...')
    base_url = 'https://steamcommunity.com/market/search/render/?q=&category_753_Game%5B%5D=any' \
               '&category_753_item_class%5B%5D=tag_item_class_5&appid=753&count=100&norender=1&sort_column=name&start='
    start = 0
    conn = sqlite3.connect('booster-packs.db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS packs (
                id INT PRIMARY KEY NOT NULL, 
                name TEXT, 
                listings INT, 
                price INT, 
                update_timestamp INT);""")
    while True:
        response = req_sess.get(base_url + str(start))
        if response.status_code != 200:
            print('Error' + str(response.status_code))
            print(response.headers)
            print(response.reason)
            print(response.cookies)
            print(response.raw)
            print(response.encoding)
            print(response.elapsed)
            break
        data = response.json()
        if data['success']:
            bulk_packs = []
            for result in data['results']:
                pack = result['hash_name'].split('-', 1)
                pack[0] = int(pack[0])
                pack.append(result['sell_listings'])
                pack.append(result['sell_price'])
                pack.append(time.time_ns())
                bulk_packs.append(pack)
        else:
            break
        cur.executemany("INSERT OR REPLACE INTO packs VALUES(?, ?, ?, ?, ?)", bulk_packs)
        conn.commit()
        start += 100
        print(start)
        # if start >= 1000:
        #     break
        if start >= data['total_count']:
            break
        time.sleep(1)
    conn.close()


def update_cards():
    print('Updating Trading Cards...')


def check_login() -> bool:
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
        print(response_logged_in.status_code)
        print(response_logged_in.headers)
        print(response_logged_in.reason)
        print(response_logged_in.cookies)
        print(response_logged_in.raw)
        print(response_logged_in.encoding)
        print(response_logged_in.elapsed)
        return False


def logout() -> bool:
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
        print(response_logout.status_code)
        print(response_logout.headers)
        print(response_logout.reason)
        print(response_logout.cookies)
        print(response_logout.raw)
        print(response_logout.encoding)
        print(response_logout.content)
        print(response_logout.elapsed)
        print(response_logout.history)
        print(response_logout.url)
        print(response_logout.links)
        return False


if __name__ == '__main__':
    with requests.Session() as req_sess:
        try:
            with open('cookies', 'rb') as f:
                req_sess.cookies.update(pickle.load(f))
        except IOError:
            pass
        menu()
        with open('cookies', 'wb') as f:
            pickle.dump(req_sess.cookies, f)
