
import AllegroScrapper
from CategoryScrapper import CategoryScrapper
from DBManager import DBManager
from multiprocessing import Pool
from Category import Category
#import colorama
import mysql.connector
from AllegroApi import AllegroApi

#total_urls_visited = 0
def Main(event,context=None):
    if __name__ == "__main__":
        #print(event['key'])

        #database = DBManager()
        #for i in range (151):
            #print(f"{database.randomProxy()} {i}")
        api = AllegroApi()
        api.auth()
        api.getCategories()
        '''
        category = CategoryScrapper()

        category.scrap(112739)'''

def scrapOffers(ID):
    all = AllegroScrapper.AllegroScrapper()
    all.scrap(ID)
    all.loadDataFromJson()
Main('a')
#Main({'key':'32100023'})

#database = DBManager()
#proxies = database.saveProxies()

