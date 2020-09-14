import requests
import base64
import colorama
import time
import csv
import os
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from bs4 import BeautifulSoup
import multiprocessing as mp
from multiprocessing import Pool


class CategoryAPIScrapper:
    def __init__(self, db):
        self.APIAccessToken = None
        self.db = db
        self.limit = 9000
        self.requestsNumber = 0
        self.maxRetries = 5
        self.retry_backoff_factor = 0.2
        self.categories = []

        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED

        self.session = requests.Session()

        self.session.proxies = {
            "http": "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "https": "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "ftp": "10.10.1.10:3128"
        }

    def setNewProxy(self):
        proxy = self.db.getProxyFromFIFO()
        self.session.proxies['http'] = proxy.replace("http", "https")
        self.session.proxies['https'] = proxy.replace("http", "https")

    def auth(self, ClientId="cb1aca5e5fbb497bb237619d7a2f9e1b",
             secret="ZIoIulPVa2aaf4gCRckBuha4DI7OL9c9ceByzMj4sg3U54tVdjOMLtPzRlZoJHj5"):
        apiCredentials = self.db.getAPICredentials()
        if apiCredentials is not None:
            apiCredentials = apiCredentials.split(',')
            print(apiCredentials)
            ClientId = apiCredentials[0]
            secret = apiCredentials[1]
        else:
            print("APICredentials are none")

        url = 'https://allegro.pl/auth/oauth/token?grant_type=client_credentials'
        authToken = f"{ClientId}:{secret}"
        encodedStr = str(base64.b64encode(authToken.encode("utf-8")), "utf-8")

        self.setNewProxy()

        print(self.session.proxies)
        response = self.session.post(url, headers={"Authorization": f"Basic {encodedStr}"})
        try:
            response = response.json()
        except Exception as e:
            print(f"{response.status_code} , {response.text}, {response.headers}")
            raise Exception(e)

        self.APIAccessToken = response["access_token"]


    def getCategories(self):
        categories = set()
        url = "https://api.allegro.pl/sale/categories"
        try:
            x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                               "accept": "application/vnd.allegro.public.v1+json"})
            response = x.json()['categories']

            self.requestsNumber += 1
        except:
            retrySucceded = False
            for retry in range(self.maxRetries):
                time.sleep(self.retry_backoff_factor * (2 ** (retry) - 1))
                self.setNewProxy()
                self.auth()
                self.requestsNumber += 1
                try:
                    x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                                       "Accept-Encoding": "br, gzip, deflate",
                                                       "accept": "application/vnd.allegro.public.v1+json"})
                    response = x.json()['categories']
                    retrySucceded = True
                    break
                except:
                    print(f'Failed {retry}/{self.maxRetries} retry to {url}')

            if retrySucceded:
                print(f'Retry to {url} succeeded.')
            else:
                raise Exception("[ERROR] Couldn't access API.")

        childCategories = []

        for i in response:
            self.categories.append([i['id'], i['name'], 0, "null"])
            print(f"{self.GREEN} [0-lev]{i['id']} - {i['name']}{self.RESET}")
            childCategories.append(i['id'])
            # print(f"{self.GREEN}{self.getChildCategories(i['id'], 1)}{self.RESET}")

        self.saveCategory()
        print(f"{self.GRAY}Starting {mp.cpu_count()} threads...{self.RESET}")
        with Pool(5) as p:
            p.map(self.getChildCategories, childCategories)

    def getChildCategories(self, id, lev=1):
        url = f"https://api.allegro.pl/sale/categories?parent.id={id}"
        try:
            x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                               "accept": "application/vnd.allegro.public.v1+json"})
            response = x.json()['categories']
            self.requestsNumber += 1
        except:
            retrySucceded = False
            for retry in range(self.maxRetries):
                time.sleep(self.retry_backoff_factor * (2 ** (retry) - 1))
                self.setNewProxy()
                self.auth()
                self.requestsNumber += 1
                try:
                    x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                                       "Accept-Encoding": "br, gzip, deflate",
                                                       "accept": "application/vnd.allegro.public.v1+json"})
                    response = x.json()['categories']
                    retrySucceded = True
                    break
                except:
                    print(f'Failed {retry}/{self.maxRetries} retry to {url}')

            if retrySucceded:
                print(f'Retry to {url} succeeded.')
            else:
                print("[ERROR] Couldn't access API.")
                return False

        for i in response:
            tab = ""
            for x in range(lev):
                tab += "\t"
            if (i is not None):
                print(f"{tab}{self.GREEN} [{lev}-lev]{i['id']} - {i['name']}{self.RESET}")
                self.categories.append([i['id'], str(i['name']), 0, i['parent']['id']])
                self.getChildCategories(i['id'], lev + 1)
        if (lev == 1):
            self.saveCategory()

    def waitIfExceeded(self):
        if (self.limit <= self.requestsNumber):
            self.saveCategory()
            print(f'{self.RED} Exceeded limit - {self.requestsNumber} requests. Waiting 60s.')
            time.sleep(60)
            self.requestsNumber = 0

    def saveCategory(self):
        fileName = f'/tmp/category.csv'
        try:
            with open(fileName, 'w', newline='', encoding='utf-8') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL, delimiter='\t')
                for c in self.categories:
                    wr.writerow(c)
        except Exception as e:
            print(e)
            fileName = f'tmp/category.csv'
            with open(fileName, 'w', newline='', encoding='utf-8') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL, delimiter='\t')
                for c in self.categories:
                    wr.writerow(c)

        print(f'{self.RED} Result exported to csv{self.RESET}')
        self.db.saveCategoryTo(fileName)
        if os.path.isfile(fileName):
            os.remove(fileName)
        print(f'{self.GREEN} Result saved to DataBase{self.RESET}')
        self.categories = []
