from bs4 import BeautifulSoup
import requests
import random
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import colorama
import json
import os
from DBManager import DBManager
import traceback
import csv

class CategoryScrapper:
    def __init__(self):
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED
        self.LIGHT_GREEN = colorama.Fore.LIGHTGREEN_EX


        self.session = requests.Session()
        self.session.proxies = {
            "http":"http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "https":"http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "ftp":"10.10.1.10:3128"
        }

        retries = Retry(total=5, backoff_factor=0.1, status_forcelist=[502, 503, 504])
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


    def scrap(self,CategoryID):
        base_link = f"https://allegro.pl/kategoria/{CategoryID}"
        proxy, agent = self.randomProxy()
        self.session.headers["User-Agent"] = agent
        self.session.proxies['http'] = proxy.replace("http", "https")
        self.session.proxies['https'] = proxy.replace("http", "https")

        link = f"{base_link}"

        reqs = self.session.get(link, allow_redirects=True)
        soup = BeautifulSoup(reqs.text, 'lxml')
        return soup


    def getNumberOfOffers(self,soup):
        if soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return int(soup.find("div", {"data-box-name": "Listing title"}).find("div").find("div").text.replace("oferta","ofert").replace("oferty","ofert").replace("ofert","").replace(" ",""))