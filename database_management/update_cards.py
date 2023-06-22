import sqlite3
import time

from helpers.print_response import print_response
from helpers.session_management import check_login


def update_cards(req_sess):
    if not check_login(req_sess):
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
                    print(f'Updated ({start}/{data["total_count"]}) Packs')
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
