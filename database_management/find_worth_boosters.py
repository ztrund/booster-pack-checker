import sqlite3

import numpy as np
import pandas as pd


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
