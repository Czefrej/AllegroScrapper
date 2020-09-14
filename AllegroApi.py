import requests
import base64
import colorama
import os
import time
from DBManager import DBManager
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import csv
import time
import json
import boto3


class AllegroApi:

    def __init__(self, db):
        sqsResource = boto3.resource('sqs')
        self.queue = sqsResource.get_queue_by_name(QueueName="CategoryQueue.fifo")
        self.APIAccessToken = None
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED

        self.lastCompletedTask = None
        self.retry_backoff_factor = 0.2
        self.maxRetries = 5
        self.limit = 9000
        self.saveTreshold = 60000
        self.saveSize = 0
        self.categories = []
        self.db = db
        self.failedTasks = []

        self.session = requests.Session()

        """
        retries = Retry(total=5, backoff_factor=0.4, status_forcelist=[502, 503, 504])
        self.session = requests.Session()
        self.session.mount('http://', HTTPAdapter(max_retries=retries))
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        """
        self.session.proxies = {
            "http": "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "https": "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.179:80",
            "ftp": "10.10.1.10:3128"
        }

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

    def setNewProxy(self):
        proxy = self.db.getProxyFromFIFO()
        self.session.proxies['http'] = proxy.replace("http", "https")
        self.session.proxies['https'] = proxy.replace("http", "https")

    def getOffers(self, CategoryID, PriceFrom=None, PriceTo=None):
        start_time = time.time()
        offset = 0
        requests = 0
        totalCount = 0
        # price.from price.to
        offersDict = dict()
        offersInIteration = None
        while True:
            if (offset == 6000):
                print(f"Finished {len(offersDict)} in {time.time() - start_time} ms")
                self.saveOffers(offersDict, CategoryID)
                break
            url = f"https://api.allegro.pl/offers/listing?category.id={CategoryID}&offset={offset}&sort=+price"

            if (PriceFrom is not None):
                url = f"{url}&price.from={PriceFrom}"

            if (PriceTo is not None):
                url = f"{url}&price.to={PriceTo}"

            try:
                x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                                   "Accept-Encoding": "br, gzip, deflate",
                                                   "accept": "application/vnd.allegro.public.v1+json"})
            except:
                retrySucceded = False
                for retry in range(self.maxRetries):
                    time.sleep(self.retry_backoff_factor * (2 ** (retry) - 1))
                    self.setNewProxy()
                    try:
                        x = self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                                           "Accept-Encoding": "br, gzip, deflate",
                                                           "accept": "application/vnd.allegro.public.v1+json"})
                        retrySucceded = True
                        break
                    except:
                        print(f'Failed {retry}/{self.maxRetries} retry to {url}')

                if retrySucceded:
                    print(f'Retry to {url} succeeded.')
                else:
                    continue


            if (x.status_code == 200):
                response = x.json()
                if (requests == 0):
                    totalCount = response['searchMeta']['totalCount']
                if 'items' in response:
                    offersInIteration = response['items']['promoted'] + response['items']['regular']
                    if (len(offersInIteration) > 0):
                        self.lastCompletedTask = offersInIteration[len(offersInIteration) - 1]['id']
                    totalCount = response['searchMeta']['totalCount']
                else:
                    print(f"Finished {len(offersDict)} in {time.time() - start_time} ms")
                    self.saveOffers(offersDict, CategoryID)
                    break
                offset += 60

                for i in offersInIteration:
                    if 'popularity' in i['sellingMode']:
                        popularity = i['sellingMode']['popularity']
                    else:
                        popularity = 0
                    offersDict[i['id']] = (
                        {'name': i['name'], 'stock': i['stock']['available'],
                         'price': i['sellingMode']['price']['amount'],
                         'original-price': i['sellingMode']['price']['amount'], 'transactions': popularity})
            else:
                self.failedTasks.append(url)
                print(url)
                self.auth()
                self.setNewProxy()
                continue
                # return {
                #
                #     'statusCode': x.status_code,
                #     'body': json.dumps(x.text),
                #     'url': url
                # }
        print(self.failedTasks)

        if self.lastCompletedTask is not None:
            print(f"{offersDict[self.lastCompletedTask]}")

            if (offset > 0):
                PriceFromFilter = float(offersDict[self.lastCompletedTask]['original-price'])
                if (PriceFrom == offersDict[self.lastCompletedTask]['original-price']):
                    PriceFromFilter += 0.01

                entry = [{'Id': str(self.lastCompletedTask),
                          'MessageBody': json.dumps({'id': str(CategoryID),
                                                     "priceFrom": PriceFromFilter,
                                                     "priceTo": None}),
                          'MessageGroupId': str(self.lastCompletedTask)}]
                response = self.queue.send_messages(Entries=entry)

        return {

            'statusCode': 200,
            'body': json.dumps(f'Done, {totalCount}/{len(offersDict)}')
        }

    def saveOffers(self, offers, CategoryID):
        fileName = f'/tmp/offers-{CategoryID}.csv'
        auctions = list()

        for o in offers:
            id = o
            o = offers[o]
            auctions.append([id, o['name'], o['original-price'], o['price'], CategoryID, o['stock'], o['transactions'],
                             o['transactions']])
        try:
            with open(fileName, 'w', newline='', encoding='utf-8') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL, delimiter='\t')
                for a in auctions:
                    wr.writerow(a)
        except Exception as e:
            print(e)
            fileName = f'tmp/offers-{CategoryID}.csv'
            with open(fileName, 'w', newline='', encoding='utf-8') as myfile:
                wr = csv.writer(myfile, quoting=csv.QUOTE_MINIMAL, delimiter='\t')
                for a in auctions:
                    wr.writerow(a)

        print(f'{self.RED} Result exported to csv{self.RESET}')

        self.db.saveOffers(f'{fileName}')
        if os.path.isfile(fileName):
            os.remove(fileName)

        print(f'{self.GREEN} Result saved to DataBase{self.RESET}')


