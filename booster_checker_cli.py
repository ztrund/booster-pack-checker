import base64
import os.path
import sqlite3
import time

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
        if input('Press 1 if you want to log out and log in again (or anything else to keep logged in): ') != '1':
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
    print('Updating Boosters...')
    base_url = 'https://steamcommunity.com/market/search/render/?q=&category_753_Game%5B%5D=any' \
               '&category_753_item_class%5B%5D=tag_item_class_5&appid=753&count=100&norender=1&sort_column=name&start='
    start = 0
    with open('cookie.txt', 'r') as cookie_file:
        cookies = {'steamLoginSecure': cookie_file.read()}
    conn = sqlite3.connect('booster-packs.db')
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS packs (
                id INT PRIMARY KEY NOT NULL, 
                name TEXT, 
                listings INT, 
                price INT, 
                update_timestamp INT);""")
    while True:
        response = requests.get(base_url + str(start), cookies=cookies)
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


if __name__ == '__main__':
    menu()
