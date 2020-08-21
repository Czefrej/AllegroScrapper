import AllegroScrapper
from CategoryScrapper import CategoryScrapper
from DBManager import DBManager
from multiprocessing import Pool
import os
#import colorama

from AllegroApi import AllegroApi
event = {}
event['Records'] = 1
#total_urls_visited = 0
def Main(event,context=None):
    if __name__ == "__main__":
        #print(event['key'])
        database = DBManager()
        categories = database.getCategories()[10:29]
        category = CategoryScrapper()
        p = Pool(int(os.environ['THREADS']))
        p.map(category.scrap, categories)
        p.close()
        p.join()
        #category.scrap(categories[0])

def scrapOffers(ID):
    all = AllegroScrapper.AllegroScrapper()
    all.scrap(ID)
    all.loadDataFromJson()
Main('a')
#Main({'key':'32100023'})

#database = DBManager()
#proxies = database.saveProxies()

