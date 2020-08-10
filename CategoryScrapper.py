from bs4 import BeautifulSoup
import requests
from requests.auth import HTTPProxyAuth
import time
import threading
import random
import colorama
import json
class CategoryScrapper:
    def __init__(self,proxyList):
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED

        self.threadData = threading.local()
        self.threadData.total = 0

        self.RequesLimitPerHour = 10
        #self.total = 0
        self.proxyList = []
        for i in proxyList:
            self.proxyList.append([0,i])

        self.offers = set()

        self.data = None
        self.totalOffers = None
        self.session = requests.Session()
        #https: // user: password @ proxyip:port

        self.user_agent_list = [
            'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36'
        ]

        self.proxies = {
            "http":"http://ypeokuao-1:9ui94tr5b0ac@",
            "https":"https://ypeokuao-1:9ui94tr5b0ac@",
            "ftp":"10.10.1.10:3128"
        }

        #self.session.auth = HTTPProxyAuth('ypeokuao-dest','9ui94tr5b0ac')
        self.session.headers = {
            "User-Agent":'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            "Accept-Encoding":"br, gzip, deflate",
            "Accept":"test/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Referer":"http://www.google.com/"}


        self.session.verify = True

    def randomProxy(self):
        proxy_index = random.randint(-1,len(self.proxyList))
        if self.proxyList[proxy_index][0] >= self.RequesLimitPerHour:
            return self.randomProxy()
        else:
            print(f"{self.GRAY}Randomed new proxy: {self.proxyList[proxy_index][1]}{self.RESET}")
            return proxy_index-1

    def scrap(self,CategoryID):
        page = 1
        base_link = f"https://allegro.pl/kategoria/{CategoryID}"
        proxy_index = self.randomProxy()
        proxy_dict = self.proxies
        proxy_dict['http'] = proxy_dict['http']+self.proxyList[proxy_index][1]
        proxy_dict['https'] = proxy_dict['https'] + self.proxyList[proxy_index][1]


        while True:
            if(self.proxyList[proxy_index][0] >= self.RequesLimitPerHour):
                print(f"{self.GRAY}Exceeded amount of requests per hour. Randoming new proxy.{self.RESET}")
                proxy_index = self.randomProxy()
                proxy_dict = self.proxies
                proxy_dict['http'] = proxy_dict['http'] + self.proxyList[proxy_index][1]
                proxy_dict['https'] = proxy_dict['https'] + self.proxyList[proxy_index][1]

            link = f"{base_link}"
            if(page > 1):
                link = f"{base_link}?p={page}"
                reqs = self.session.get(link, allow_redirects=False, proxies=proxy_dict)
                self.session.headers['User-Agent'] = random.choice(self.user_agent_list)
                '''
                try:
                    reqs = self.session.get(link, allow_redirects=False,proxies=proxy_dict)
                except:
                    print(f'{self.RED}[Failed] {link} via {self.proxyList[proxy_index][1]}{self.RESET}')
                '''

            else:
                reqs = self.session.get(link, allow_redirects=True, proxies=proxy_dict)
                '''
                try:
                    reqs = self.session.get(link,allow_redirects=True,proxies=proxy_dict)
                except:
                    print(f'{self.RED}[Failed] {link} via {self.proxyList[proxy_index][1]}{self.RESET}')
                '''
                base_link = reqs.url
            if(reqs.status_code) == 301 & page > 1 :
                page -=1
                print(f"{self.RED}[>] Found {page} pages of category {CategoryID}")
                break
            else:
                print(f"{self.GREEN}[{reqs.status_code}] Category link: {link}  > {self.threadData.total}{self.RESET}")
                self.soup = BeautifulSoup(reqs.text, 'lxml')

            if(reqs.status_code == 429):
                print(reqs.headers)
            if page == 1:
                try:
                    self.totalOffers = self.getNumberOfOffers()
                except:
                    print(link)
                print(f"{self.GRAY} Found {self.totalOffers} offers{self.RESET}")
            page += 1
            self.threadData.localtotal+=1
            self.proxyList[proxy_index][0]+=1

    def getNumberOfOffers(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            return int(self.soup.find("div", {"data-box-name": "Listing title"}).find("div").find("div").text.replace("oferta","ofert").replace("oferty","ofert").replace("ofert","").replace(" ",""))

    def getJSON(self):
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            try:
                self.data = json.loads(str(self.soup.find("script", {"data-serialize-box-name": "items-v3"}).text))["__listing_StoreState_base"]
            except:
                raise Exception("Website is empty")
            #print(json.dumps(self.data,indent=4,sort_keys=True))

    def loadDataFromJson(self):
        products = set()
        if self.soup is None:
            raise Exception("Soup cannot be None - use scrap method first")
        else:
            self.getJSON()
            for i in self.data["items"]["itemsGroups"]:
                for x in i["items"]:
                    products.add(x['id'])

        print(f"{self.GRAY} Znaleziono {len(products)} produktów {self.RESET}")