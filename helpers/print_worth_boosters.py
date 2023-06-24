import sqlite3

import pandas as pd


def print_worth_boosters():
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', None)
    pd.set_option('display.max_colwidth', None)
    with sqlite3.connect('booster-packs.db') as conn:
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='worth_boosters';")
        if cur.fetchone() is None:
            print("Please run '4.Find Boosters That Are Worth It' before this to create 'worth_boosters' table")
            return
        while True:
            num = input('How many booster packs should I return? ')
            if num.isdigit():
                num = int(num)
                if num > 0:
                    break
            print("Please input a number greater than 0")
        df = pd.read_sql_query(f"SELECT * FROM worth_boosters ORDER BY non_foil_return DESC LIMIT {num};", conn)
        print(df)
