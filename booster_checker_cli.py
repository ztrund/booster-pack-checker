import base64
import pickle
import sqlite3
import time

import numpy as np
import requests
import rsa
import pandas as pd


def menu():  # Temporary cli menu until I build gui
    while True:
        print('1.Login to Steam (Increases Update Rate Significantly)')
        print('2.Update Games List and Booster Pack Prices')
        print('3.Update Trading Card Prices')
        print('4.Find Boosters That Are Worth It')
        print('5.Check Login Status')
        print('6.Logout of Steam')
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
                find_worth_boosters()
            case '5':
                check_login()
            case '6':
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


def update_boosters():
    if not check_login():
        if input(
                'It looks like you are not logged in, the update rate will be significantly slower (Press 1 if you wish'
                ' to continue without logging in):') != '14':
            return
    print('Updating Boosters...')
    base_url = 'https://steamcommunity.com/market/search/render/?q=&category_753_Game%5B%5D=any' \
               '&category_753_item_class%5B%5D=tag_item_class_5&appid=753&count=100&norender=1&sort_column=name&start='
    start = 0
    retry_attempts = 0
    with sqlite3.connect('booster-packs.db') as conn:
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
                print_response(response)
                break
            data = response.json()
            if data['success']:
                if int(data['total_count']) > 0:
                    retry_attempts = 0
                    bulk_packs = []
                    for result in data['results']:
                        pack = result['hash_name'].split('-', 1)
                        pack[0] = int(pack[0])
                        pack.append(result['sell_listings'])
                        pack.append(result['sell_price'])
                        pack.append(time.time_ns())
                        bulk_packs.append(pack)
                    cur.executemany("INSERT OR REPLACE INTO packs VALUES(?, ?, ?, ?, ?)", bulk_packs)
                    conn.commit()
                    start += 100
                    print('Updated (' + str(start) + '/' + str(data['total_count']) + ') Packs')
                    # if start >= 1000:
                    #     break
                    if start >= data['total_count']:
                        print('Updating Packs Complete')
                        break
                else:
                    retry_attempts += 1
                    if retry_attempts <= 10:
                        print('Invalid Total Count Received Retrying...(' + str(retry_attempts) + '/10)')
                    else:
                        break
                time.sleep(.1)
            else:
                print_response(response)
                break


def update_cards():
    if not check_login():
        if input(
                'It looks like you are not logged in, the update rate will be significantly slower (Press 1 if you wish'
                ' to continue without logging in):') != '1':
            return
    print('Updating Trading Cards...')
    base_url = 'https://steamcommunity.com/market/search/render?q=&category_753_Game%5B%5D=any' \
               '&category_753_item_class%5B%5D=tag_item_class_2&appid=753&count=100&norender=1&sort_column=name&start='
    start = 0
    retry_attempts = 0
    with sqlite3.connect('booster-packs.db') as conn:
        cur = conn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS cards (
                        game_id INT NOT NULL, 
                        name TEXT, 
                        is_foil INT, 
                        listings INT, 
                        price INT, 
                        update_timestamp INT, 
                        PRIMARY KEY (game_id, name), 
                        FOREIGN KEY (game_id) REFERENCES packs(id));""")
        while True:
            response = req_sess.get(base_url + str(start))
            if response.status_code != 200:
                print_response(response)
                break
            data = response.json()
            if data['success']:
                if int(data['total_count']) > 0:
                    retry_attempts = 0
                    bulk_cards = []
                    for result in data['results']:
                        card = result['hash_name'].split('-', 1)
                        card[0] = int(card[0])
                        card.append(1 if 'Foil Trading Card' in result['asset_description']['type'] else 0)
                        card.append(result['sell_listings'])
                        card.append(result['sell_price'])
                        card.append(time.time_ns())
                        bulk_cards.append(card)
                    cur.executemany("INSERT OR REPLACE INTO cards VALUES(?, ?, ?, ?, ?, ?)", bulk_cards)
                    conn.commit()
                    start += 100
                    print('Updated (' + str(start) + '/' + str(data['total_count']) + ') Cards')
                    # if start >= 1000:
                    #     break
                    if start >= data['total_count']:
                        print('Updating Cards Complete')
                        break
                else:
                    retry_attempts += 1
                    if retry_attempts <= 10:
                        print('Invalid Total Count Received Retrying...(' + str(retry_attempts) + '/10)')
                    else:
                        break
                time.sleep(.1)
            else:
                print_response(response)
                break


def estimate_return(price):
    if price < 22:
        return price - 2
    elif price == 22:
        return 19
    else:
        estimated_return = price
        while estimated_return > 0:
            adjustment = np.floor(estimated_return * 0.05) + np.floor(estimated_return * 0.10)
            if estimated_return + adjustment == price:
                return estimated_return
            else:
                estimated_return -= 1
        return None  # If no valid return estimate could be found


def find_worth_boosters():
    # connect to the database
    with sqlite3.connect('booster-packs.db') as conn:
        # drop the 'worth_boosters' table if it exists
        conn.execute("DROP TABLE IF EXISTS worth_boosters")

        # query to get packs with listings >= 5
        packs_query = """
        SELECT p.id pack_id, p.name pack_name, p.price pack_price
        FROM packs p
        WHERE p.listings >= 5
        """
        packs_df = pd.read_sql_query(packs_query, conn)

        # query to get cards where all the cards with the same game_id have listings >=5
        cards_query = """
        SELECT c.game_id, c.is_foil, c.price card_price
        FROM cards c
        WHERE c.game_id IN (
            SELECT game_id
            FROM cards
            GROUP BY game_id
            HAVING MIN(listings) >= 5 AND
                   COUNT(CASE WHEN is_foil = 1 THEN 1 END) = COUNT(CASE WHEN is_foil = 0 THEN 1 END)
        )
        """
        cards_df = pd.read_sql_query(cards_query, conn)

        # estimate return for each card
        cards_df['estimated_return'] = cards_df['card_price'].apply(estimate_return)

        # calculate average price for each 'game_id' and 'is_foil' combination
        avg_cards = cards_df.groupby(['game_id', 'is_foil']).card_price.mean().unstack().reset_index().rename(
            columns={0: 'non_foil_price', 1: 'foil_price'})

        # merge the packs data with the averages
        merged = pd.merge(packs_df, avg_cards, left_on='pack_id', right_on='game_id')

        # calculate the returns
        merged['non_foil_return'] = merged['non_foil_price'] * 3 - merged['pack_price']
        merged['with_foil_total'] = (merged['non_foil_price'] * .99 + merged['foil_price'] * .01) * 3 - merged[
            'pack_price']

        # filter where 'non_foil_return' > 0
        filtered = merged[merged['non_foil_return'] > 0].sort_values('non_foil_return', ascending=False)

        # drop unwanted columns
        filtered = filtered.drop(columns=['game_id', 'non_foil_price', 'foil_price'])

        # store the results in a new table 'results' in the SQLite database
        filtered.to_sql('worth_boosters', conn, if_exists='replace', index=False)


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
        print_response(response_logged_in)
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
        print_response(response_logout)
        return False


def print_response(resp: requests.Response):
    print(resp.status_code)
    print(resp.headers)
    print(resp.reason)
    print(resp.cookies)
    print(resp.raw)
    print(resp.encoding)
    print(resp.content)
    print(resp.elapsed)
    print(resp.history)
    print(resp.url)
    print(resp.links)


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
