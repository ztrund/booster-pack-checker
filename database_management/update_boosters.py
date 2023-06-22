import sqlite3
import time

from helpers.print_response import print_response
from helpers.session_management import check_login


def update_boosters(req_sess):
    if not check_login(req_sess):
        if input(
                'It looks like you are not logged in, the update rate will be significantly slower (Press 1 if you wish'
                ' to continue without logging in):') != '1':
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
            response = req_sess.get(f"{base_url}{start}")
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
