from bs4 import BeautifulSoup
import grequests
import requests
import time
import json
import colorama
import re
class AllegroScrapper:
    def __init__(self):
        self.soup = None
        colorama.init()
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED
        self.owner = None
        self.price = None
        self.quantity = None
        self.sold = None
        self.originalPrice = None

    def scrap(self,OfferID):
        links = [f"https://allegro.pl/oferta/{OfferID}",
                 f"https://allegro.pl/oferta/{OfferID}",
                 ]
        reqs = [grequests.get(link) for link in links]
        resp = grequests.map(reqs)
        for r in resp:
            self.soup = BeautifulSoup(r.text, 'lxml')
        return True

    def getName(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("button", {"data-item-title": True})["data-item-title"])

    def getOwner(self):
        if self.owner is not None:
            print(self.owner)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("a", {"data-analytics-click-value": 'sellerLogin'}).text.split(' ')[0])

    def getCustomerNumber(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("a", {"data-analytics-click-value": 'sellerLogin'}).text.split(' ')[0])

    def getJSON(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            self.data = json.loads(str(self.soup.find("script", {"data-serialize-box-name": "summary"}).text))
            print(json.dumps(self.data,indent=4,sort_keys=True))


    def loadDataFromJson(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            self.getJSON()
            self.owner = self.data["sellerLogo"]["sellerName"]
            self.price = int(self.data["price"]["priceInteger"]) + (int(self.data["price"]["priceFraction"])/100)
            self.quantity = int(self.data["transactionSection"]["availableQuantity"]["value"])
            if self.data["notifyAndWatch"]["sellingMode"]["buyNow"]["price"]["original"] is not None:
                self.originalPrice = float(str(self.data["notifyAndWatch"]["sellingMode"]["buyNow"]["price"]["original"]["amount"]))
            else:
                self.originalPrice = 0

            if self.data["popularity"]["label"] is not None:
                self.transactions = int(str(self.data["popularity"]["label"].split(" ")[0]))
                self.sold = int(str(self.data["popularity"]["label"]).split(" ")[3])
            else:
                self.transactions = 0
                self.sold = 0



    def getTransactionsNumber(self):
        if self.transactions is not None:
            print(self.transactions)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return 0

    def getSold(self):
        if self.sold is not None:
            print(self.sold)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return 0

    def getOriginalPrice(self):
        if self.originalPrice is not None:
            print(self.originalPrice)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return 0


    def getPrice(self):
        if self.price is not None:
            print(self.price)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("meta", {"itemprop" : "price"})["content"])

    def getQuantity(self):
        if self.quantity is not None:
            print(self.quantity)
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return 0

    def getName2(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("meta", {"itemprop" : "name"})["content"])