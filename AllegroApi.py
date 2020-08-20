import requests
import base64
import json
import colorama
import os
import time
import pandas as pd
from DBManager import DBManager
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

class AllegroApi:

    def __init__(self):
        self.accessToken = None
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED
        self.requestsNumber = 0
        self.limit = 9000
        self.categories = []

        retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))

    def auth(self, ClientId="48b436cf19624df6ab6788d592ffa2ac", secret="A2uN76nR7FdNju3WNq8xj8X3Po45Nv3R0F5JtazNXjYT8u605dZRMDM9OMApXnBS"):
        url = 'https://allegro.pl/auth/oauth/token?grant_type=client_credentials'
        authToken = f"{ClientId}:{secret}"
        encodedBytes = base64.b64encode(authToken.encode("utf-8"))
        encodedStr = str(encodedBytes, "utf-8")
        x = requests.post(url, headers={"Authorization": f"Basic {encodedStr}"})
        data = x.json()
        self.accessToken = data["access_token"]
        self.saveToken()
        self.requestsNumber +=1

    def getCategories(self):
        self.waitIfExceeded()
        categories = set()
        url = "https://api.allegro.pl/sale/categories"
        x = self.session.get(url, headers={"Authorization": f"Bearer {self.accessToken}","accept":"application/vnd.allegro.public.v1+json"})
        self.requestsNumber +=1
        response = x.json()['categories']
        for i in response:
            self.categories.append([i['id'],i['name'],"null"])
            print(f"{self.GREEN} [0-lev]{i}{self.RESET}")
            print(f"{self.GREEN}{self.getChildCategories(i['id'],1)}{self.RESET}")


    def getChildCategories(self,id,lev):
        self.waitIfExceeded()
        categories = set()
        url = f"https://api.allegro.pl/sale/categories?parent.id={id}"
        x = self.session.get(url, headers={"Authorization": f"Bearer {self.accessToken}",
                                       "accept": "application/vnd.allegro.public.v1+json"})
        self.requestsNumber +=1
        response = x.json()
        for i in response['categories']:
            tab = ""
            for x in range(lev):
                tab += "\t"
            if(i is not None):
                print(f"{tab}{self.GREEN} [{lev}-lev]{i}{self.RESET}")
                self.categories.append([i['id'], str(i['name']), i['parent']['id']])
                self.getChildCategories(i['id'],lev+1)


    def waitIfExceeded(self):
        if(self.limit <= self.requestsNumber):
            df = pd.DataFrame(self.categories)
            df.to_csv('categories.csv', encoding='utf-8', index=False,sep="\t",header=['ID','Name','Parent-id'])
            print(f'{self.RED} Result exported to csv{self.RESET}')
            db = DBManager()
            db.saveCategoryTo()
            print(f'{self.GREEN} Result saved to DataBase{self.RESET}')
            self.categories = []
            print(f'{self.RED} Exceeded limit - {self.requestsNumber} requests. Waiting 60s.')
            time.sleep(60)
            self.requestsNumber = 0



    def saveToken(self):
        f = open("token.txt", "w")
        f.write(self.accessToken)
        f.close()