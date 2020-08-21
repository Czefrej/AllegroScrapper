from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPProxyAuth
import time
import threading
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import colorama
import json
import os
from DBManager import DBManager
import traceback
import pandas as pd


class CategoryScrapper:
    def __init__(self):
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED

        self.RequestLimitPerProxy = 10


        #self.total = 0

        self.offers = set()

        self.totalOffers = None

        self.session = requests.Session()
        self.session.proxies = {
            "http":"http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "https":"http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "ftp":"10.10.1.10:3128"
        }

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

        self.session.headers = {
            "User-Agent":'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            "Accept-Encoding":"br, gzip, deflate",
            "Accept":"test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer":"http://www.google.com/"}
        self.session.verify = True

    def randomProxy(self):
        db = DBManager()
        proxy_agent = db.randomProxy()
        proxy,agent = str(proxy_agent).split('|')

        return proxy,agent

    def randomLimitPerProxy(self,From = int(os.environ['REQ_PER_PROXY_FLOOR']),To = int(os.environ['REQ_PER_PROXY_CEIL'])):
        n = random.randint(From, To)
        return n

    def scrap(self,CategoryID):
        offers = dict()
        totalOffers = 0
        page = 1
        requests = 0
        self.RequestLimitPerProxy = self.randomLimitPerProxy()
        base_link = f"https://allegro.pl/kategoria/{CategoryID}"
        proxy,agent = self.randomProxy()
        self.session.headers["User-Agent"] = agent
        self.session.proxies['http'] = proxy.replace("http", "https")
        self.session.proxies['https'] = proxy.replace("http","https")


        while True:
            if(requests >= self.RequestLimitPerProxy):
                requests = 0
                self.RequestLimitPerProxy = self.randomLimitPerProxy()
                proxy, agent = self.randomProxy()
                print(f"{self.GRAY}Exceeded amount of requests per proxy. Randoming new proxy. > {proxy}{self.RESET}")
                self.session.headers["User-Agent"] = agent
                self.session.proxies['http'] = proxy.replace("http", "https")
                self.session.proxies['https'] = proxy.replace("http", "https")

            link = f"{base_link}"
            try:
                if(page > 1):
                    link = f"{base_link}?p={page}"
                    reqs = self.session.get(link, allow_redirects=False)

                else:
                    reqs = self.session.get(link, allow_redirects=True)
                    base_link = reqs.url
                if reqs.status_code == 301 and page > 1:
                    page -= 1
                    print(f"{self.RED}[>] Found {page} pages of category {CategoryID}")
                    break
                else:
                    print(
                        f"{self.GREEN}[{reqs.status_code}] Category link: {link}  > {self.session.proxies['https']} {page}{self.RESET}")
                    soup = BeautifulSoup(reqs.text, 'lxml')
                    offers = self.getOffers(soup,offers)
                if (reqs.status_code == 429):
                    print(reqs.headers)
                if page == 1:
                    try:
                        totalOffers = self.getNumberOfOffers(soup)
                    except:
                        print(link)
                    print(f"{self.GRAY} Found {totalOffers} offers{self.RESET}")

                    #if(totalOffers/60 > 100):
                        #print(totalOffers)


            except Exception as e:
                print(f"{self.RED}[FAILED] Category link: {link}  > {self.session.proxies['https']}/{self.session.headers['User-Agent']}{self.RESET}")
                print(e)
                print(traceback.print_tb(e.__traceback__))
            page += 1
            requests += 1

        self.saveOffers(offers, CategoryID)



    def getNumberOfOffers(self,soup):
        if soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return int(soup.find("div", {"data-box-name": "Listing title"}).find("div").find("div").text.replace("oferta","ofert").replace("oferty","ofert").replace("ofert","").replace(" ",""))

    def getJSON(self,soup):
        if soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            try:
                data = json.loads(soup.find("script", {"data-serialize-box-name": "items-v3"}).string)
                data = json.loads(data["__listing_StoreState_base"])
            except:
                data = json.loads(soup.find("script", {"data-serialize-box-name": "items-v3"}).string)
                data = json.loads(data["__listing_StoreState_base-mobile"])
            return data

    def getOffers(self,soup,offers):
        data = self.getJSON(soup)['items']['elements']
        for i in data:
            if 'id' in i:
                if i["bidInfo"] and "nikt" not in i["bidInfo"].lower():
                    transactions = int(i["bidInfo"].split(' ')[0])
                else:
                    transactions = 0

                if i['id'] not in offers:
                    offers[i['id']] = {'name': i['title']['text'],'stock':i['quantity'],'price':i['price']['normal']['amount'],'original-price':0,'transactions':transactions}
        return offers


    def saveOffers(self,offers,CategoryID):
        auctions = list()

        for o in offers:
            id = o
            o = offers[o]
            auctions.append([id,o['name'],o['original-price'],o['price'],CategoryID,o['stock'],o['transactions'],o['transactions']])

        df = pd.DataFrame(auctions)
        df.to_csv(f'offers-{CategoryID}.csv', encoding='utf-8', index=False, header=None, sep="\t")
        print(f'{self.RED} Result exported to csv{self.RESET}')
        db = DBManager()
        db.saveOffers(f'offers-{CategoryID}.csv')
        print(f'{self.GREEN} Result saved to DataBase{self.RESET}')