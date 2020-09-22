import requests
import base64
import colorama
import os
import random
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import csv
import time
import json
import boto3


class AllegroApi:

    def __init__(self, proxies,APICredentials):
        sqsResource = boto3.resource('sqs')
        self.categoryQueue = sqsResource.get_queue_by_name(QueueName="CategoryQueue.fifo")
        self.databaseQueue = sqsResource.get_queue_by_name(QueueName="TradeDataSavingQueue.fifo")
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

        self.proxies = proxies
        self.APICredentials = APICredentials

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

        apiCredentials = random.choice(self.APICredentials)
        if apiCredentials is not None:
            ClientId = apiCredentials[0]
            secret = apiCredentials[1]
        else:
            print("APICredentials are none")

        url = 'https://allegro.pl/auth/oauth/token?grant_type=client_credentials'
        authToken = f"{ClientId}:{secret}"
        encodedStr = str(base64.b64encode(authToken.encode("utf-8")), "utf-8")

        print(self.session.proxies)
        response = self.session.post(url, headers={"Authorization": f"Basic {encodedStr}"})
        try:
            response = response.json()
        except Exception as e:
            print(f"{response.status_code} , {response.text}, {response.headers}")
            raise Exception(e)

        self.APIAccessToken = response["access_token"]

    def setNewProxy(self):
        proxy = random.choice(self.proxies)[0]
        self.session.proxies['http'] = proxy.replace("http", "https")
        self.session.proxies['https'] = proxy.replace("http", "https")

    def sendAPIRequest(self, url):
        return self.session.get(url, headers={"Authorization": f"Bearer {self.APIAccessToken}",
                                              "Accept-Encoding": "br, gzip, deflate",
                                              "accept": "application/vnd.allegro.public.v1+json"})

    def getOffers(self, CategoryID, offset=0, PriceFrom=None, PriceTo=None):
        offersList = []
        offersInIteration = []
        available = 0
        url = f"https://api.allegro.pl/offers/listing?category.id={CategoryID}&offset={offset}&sort=+price"

        if (PriceFrom is not None):
            url = f"{url}&price.from={PriceFrom}"

        if (PriceTo is not None):
            url = f"{url}&price.to={PriceTo}"

        x = self.retryOnFail(self.sendAPIRequest, "Failed to fetch data.", True, url)
        if (x.status_code == 200):
            try:
                response = x.json()
                if 'items' in response:
                    offersInIteration = response['items']['promoted'] + response['items']['regular']
                if 'searchMeta' in response:
                    available = int(response['searchMeta']['availableCount'])

                for i in offersInIteration:
                    if i['sellingMode']['format'] == "BUY_NOW" or i['sellingMode']['format'] == "AUCTION":
                        if (i['sellingMode']['format'] == "BUY_NOW"):
                            if 'popularity' in i['sellingMode']:
                                popularity = i['sellingMode']['popularity']
                            else:
                                popularity = 0
                        else:
                            if 'popularity' in i['sellingMode']:
                                popularity = i['sellingMode']['bidCount']
                            else:
                                popularity = 0
                        img_url = None
                        if 'images' in i:
                            if (len(i['images']) > 0):
                                img_url = i['images'][0]['url']
                        if 'puiblication' in i:
                            endingAt = i['publication']['endingAt']
                        else:
                            endingAt = 0

                        seller_login = "unknown"
                        if 'login' in i['seller']:
                            seller_login = i['seller']['login']
                        offersList.append(
                            {'id': i['id'],
                             'name': i['name'],
                             'stock': i['stock']['available'],
                             'price': i['sellingMode']['price']['amount'],
                             'transactions': popularity,
                             'offerType': i['sellingMode']['format'],
                             'promotion': {
                                 'emphasized': i['promotion']['emphasized'],
                                 'bold': i['promotion']['bold'],
                                 'highlight': i['promotion']['highlight']
                             },
                             'seller': {
                                 'id': i['seller']['id'],
                                 'login': seller_login,
                                 'superSeller': i['seller']['superSeller'],
                                 'company': i['seller']['company']
                             },
                             'imgURL': img_url,
                             'delivery': {
                                 'availableForFree': i['delivery']['availableForFree'],
                                 'lowestPrice': i['delivery']['lowestPrice']
                             },
                             'endingAt': endingAt
                             })



            except Exception as e:
                print(e)
                print(f"ERROR {x.text}")
        else:
            self.failedTasks.append(url)
            print(url)
            self.auth()
            self.setNewProxy()

        return offersList, available

    def searchForOffersRecurrently(self, CategoryID, PriceFrom=0, PriceTo=None):
        print(f"Scrapping {CategoryID}")
        self.setNewProxy()
        self.retryOnFail(self.auth, "Failed to Authenticate")
        if (PriceFrom == 0):
            notFullResponseCount = 0
            currentPrice = PriceFrom
            offset = 5940
            step = 60
            priceStep = 0.01
            total = 0
            skip = False
            while True:
                offersList, available = self.getOffers(CategoryID, offset, currentPrice, PriceTo)

                if (len(offersList) == 0):
                    while True:
                        if (offset < 0):
                            skip = True
                            break
                        offersList, available = self.getOffers(CategoryID, offset, currentPrice, PriceTo)
                        if (available == 0):
                            break
                        if (len(offersList) > 0):
                            break
                        offset = available - 1

                    if (notFullResponseCount > 3):
                        break
                    notFullResponseCount += 1
                if skip:
                    break

                if (len(offersList) > 0):
                    newPrice = float(offersList[len(offersList) - 1]['price'])
                    if (newPrice < currentPrice):
                        priceStep += 1
                    if (currentPrice == newPrice):
                        newPrice += priceStep

                    currentPrice = newPrice

                    total += available

                    print(f"Found {len(offersList) + offset} at price < {currentPrice} ")

                    entry = [{'Id': str(f"{CategoryID}x{offersList[len(offersList) - 1]['id']}"),
                              'MessageBody': json.dumps({'id': str(CategoryID),
                                                         "priceFrom": currentPrice,
                                                         "priceTo": None, "apis": self.APICredentials,
                                                         "proxies": self.proxies}),
                              'MessageGroupId': str(f"{CategoryID}x{offersList[len(offersList) - 1]['id']}")}]
                    # response = self.categoryQueue.send_messages(Entries=entry)


                else:
                    break
            print(f"Found {total} in total.")
        joinedOfferList = []
        offset = 0
        for i in range(100):
            offersList, available = self.getOffers(CategoryID, offset, PriceFrom, PriceTo)
            if (len(offersList) > 0):
                joinedOfferList = joinedOfferList + offersList
            else:
                break
            offset += 60
        if (len(joinedOfferList) > 0):
            self.saveOffersToSQS(joinedOfferList, CategoryID)
        print(self.failedTasks)
        return {

            'statusCode': 200,
            'body': json.dumps(f'Done, {len(joinedOfferList)}')
        }


    def saveOffersToSQS(self, offers, CategoryID):
        dataChunk = 40
        maxEntries = 10
        auctions = []
        entries = []
        c = 0
        messages = 0
        for o in offers:
            auctions.append(
                o)
            c += 1
            if(c == dataChunk):
                entries.append({'Id': str(f"{CategoryID}x{messages}"),
                                'MessageBody': json.dumps({'id': str(CategoryID),
                                                           'data': auctions}),
                                'MessageGroupId': str(CategoryID)})
                messages += 1
                auctions = []
                c = 0

            if(len(entries) == maxEntries):
                self.databaseQueue.send_messages(Entries=entries)
                entries = []

        if (len(auctions) != 0):
            entries.append({'Id': str(f"{CategoryID}-{messages}"),
                            'MessageBody': json.dumps({'id': str(CategoryID),
                                                       'data': auctions}),
                            'MessageGroupId': str(CategoryID)})

            messages += 1
        # if (len(entries) != 0):
        #     response = self.databaseQueue.send_messages(Entries=entries)
        print(entries[0])
        print(f'{self.GREEN} Result sent to DataBase Queue{self.RESET}')

    def retryOnFail(self, callable, failMessage, reauth=False, *args):
        result = False
        try:
            self.setNewProxy()
            result = callable(*args)
        except:
            retrySucceded = False
            for retry in range(self.maxRetries):
                time.sleep(self.retry_backoff_factor * (2 ** (retry) - 1))
                self.setNewProxy()
                try:
                    result = callable(*args)
                    retrySucceded = True
                    break
                except Exception as e:
                    print(f'{failMessage} {retry}/{self.maxRetries}')
                    if (reauth):
                        self.retryOnFail(self.auth, "Failed to Authenticate")
            if not retrySucceded:
                result = {
                    'statusCode': 429,
                    'body': json.dumps(f'{failMessage}')
                }

        return result
