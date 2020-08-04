from bs4 import BeautifulSoup
import grequests
import requests
import time
class AllegroScrapper:
    def __init__(self):
        self.soup = None
    def scrap(self,OfferID):
        links = [f"https://allegro.pl/oferta/{OfferID}",
                 f"https://allegro.pl/oferta/{OfferID}",
                 ]
        reqs = [grequests.get(link) for link in links]
        resp = grequests.map(reqs)
        for r in resp:
            self.soup = BeautifulSoup(r.text, 'lxml')
        return True

    def getPrice(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("button", {"data-item-price" : True})["data-item-price"])
    def getName(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("button", {"data-item-title": True})["data-item-title"])


    def getPrice2(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("meta", {"itemprop" : "price"})["content"])

    def getName2(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            print(self.soup.find("meta", {"itemprop" : "name"})["content"])