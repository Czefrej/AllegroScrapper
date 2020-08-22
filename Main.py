import AllegroScrapper
from CategoryScrapper import CategoryScrapper
from DBManager import DBManager
from multiprocessing import Pool
import os
import colorama


def Main(event,context=None):
    if __name__ == "Main":
        threads = int(os.environ['THREADS'])
        #print(event['key'])
        database = DBManager()
        #for i in event['']
        categories = database.getCategories()[13:14]
        print(categories)
        category = CategoryScrapper()
        print(f"{colorama.Fore.CYAN}Launching {threads} threads.{colorama.Fore.RESET}")
        if len(categories) < threads:
            p = Pool(len(categories))
        else:
            p = Pool(threads)
        p.map(category.scrap, categories)
        p.close()
        p.join()
        #category.scrap(categories[0])


