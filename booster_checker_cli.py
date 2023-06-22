import pickle
import requests

from database_management.find_worth_boosters import find_worth_boosters
from database_management.update_boosters import update_boosters
from database_management.update_cards import update_cards
from helpers.session_management import login, check_login, logout


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
                login(req_sess)
            case '2':
                update_boosters(req_sess)
            case '3':
                update_cards(req_sess)
            case '4':
                find_worth_boosters()
            case '5':
                check_login(req_sess)
            case '6':
                logout(req_sess)
            case '0':
                print('Exiting Program...')
                break
            case _:
                print('INVALID SELECTION')


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
