import AllegroScrapper
from CategoryScrapper import CategoryScrapper
from DBManager import DBManager
from multiprocessing import Pool
import os
from AllegroApi import AllegroApi
import json
import colorama

db = None

def Main(event,context=None):
    if __name__ == "__main__" or __name__ == "Main":
        print(event['Records'][0]['body'])
        print('Connecting to database....')
        db = DBManager(remote=True)
        print("Connected!")
        allegro = AllegroApi(db)
        allegro.auth()
        response = allegro.getOffers(event['Records'][0]['body'])

        return response

#Main({"Records":[{"body":12}]})