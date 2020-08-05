
import AllegroScrapper
import CategoryScrapper
from multiprocessing import Pool
import lxml
#import colorama

# init the colorama module
#colorama.init()

#GREEN = colorama.Fore.GREEN
#GRAY = colorama.Fore.LIGHTBLACK_EX
#RESET = colorama.Fore.RESET
#RED = colorama.Fore.RED

# initialize the set of links (unique links)
#internal_urls = set()
#external_urls = set()
#category_links = set()
#threads = set()

#total_urls_visited = 0
if __name__ == '__main__':
    #cat = CategoryScrapper.CategoryScrapper()
    #p = Pool(10)
    #p.map(cat.scrap,"karmy-mokra-karma-90062")
    #p.terminate()
    #p.join()
    all = AllegroScrapper.AllegroScrapper()
    all.scrap(9039523750)
    all.getName2()
    all.loadDataFromJson()
    all.getOriginalPrice()

    all.getPrice()
    all.getOwner()
    #all.getTransactionsNumber()

    #all.getJSON()
    all.scrap(6850814534)
    all.loadDataFromJson()
    all.getName2()
    all.getOwner()
    all.getQuantity()
    all.getTransactionsNumber()
    all.getSold()
    all.getOriginalPrice()