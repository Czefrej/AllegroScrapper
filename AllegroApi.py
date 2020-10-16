import traceback

import requests
import base64
import os
import random
import string
import sys
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import time
import json
import boto3


class AllegroApi:

    def __init__(self, proxies,APICredentials):
        sqsResource = boto3.resource('sqs')
        self.categoryQueue = sqsResource.get_queue_by_name(QueueName="CategoryQueue.fifo")
        self.databaseQueues = [
            sqsResource.get_queue_by_name(QueueName="TradeDataSavingQueue.fifo"),
            sqsResource.get_queue_by_name(QueueName="TradeDataSavingQueue2.fifo")]
        self.APIAccessToken = None

        self.lastCompletedTask = None
        self.retry_backoff_factor = 0.1
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
            print(f"Authenticating with {ClientId} {secret}")
        else:
            print("APICredentials are none")

        url = 'https://allegro.pl/auth/oauth/token?grant_type=client_credentials'
        authToken = f"{ClientId}:{secret}"
        encodedStr = str(base64.b64encode(authToken.encode("utf-8")), "utf-8")

        print(self.session.proxies)
        response = self.session.post(url, headers={"Authorization": f"Basic {encodedStr}"})
        try:
            response = response.json()
            self.APIAccessToken = response["access_token"]
        except Exception as e:
            print(f"Size of message: {sys.getsizeof(response.text)} Headers : {response.status_code} , {response.text}, {response.headers}")
            raise Exception(e)

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
        x = self.retryOnFail(self.sendAPIRequest, "Failed to fetch data.", True, url=url)[0]
        if (x.status_code == 200):
            response = x.json()
            if 'items' in response:
                for i in response['items']['promoted']:
                    i['promoted'] = True
                offersInIteration = response['items']['promoted'] + response['items']['regular']
            if 'searchMeta' in response:
                available = int(response['searchMeta']['availableCount'])

            for i in offersInIteration:
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

                if 'promoted' in i:
                    promoted = True
                else:
                    promoted = False

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
                         'promoted': promoted,
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
                     'endingAt': endingAt,
                     'creation_date': time.strftime('%Y-%m-%d %H:%M:%S')
                     })
        else:
            raise Exception(f"Received {x.status_code} response")
        return offersList, available


    def generateDeduplicationToken(self, N=9):
        return ''.join(random.choices(string.ascii_uppercase + string.digits, k=N))

    def searchForOffersRecurrently(self, CategoryID=0, PriceFrom=0, PriceTo=None, resume=False):
        func_begin_time = time.time()
        print(f"Scrapping {CategoryID} in price range {PriceFrom} - {PriceTo}")
        self.setNewProxy()
        self.retryOnFail(self.auth, "Failed to Authenticate")
        if(not resume):
            if (PriceFrom == 0):
                i = 0
                notFullResponseCount = 0
                currentPrice = PriceFrom
                offset = 5940
                step = 60
                priceStep = 0.01
                total = 0
                skip = False
                while True:
                    start_time = time.time()
                    offersList, available = self.retryOnFail(self.getOffers,f"Failed to get offers at {CategoryID} at price range {currentPrice} - {PriceTo}[{offset}]",reauth=True,double_return=True,CategoryID = CategoryID, offset = offset, PriceFrom=currentPrice, PriceTo=PriceTo)
                    print(offersList)
                    if(offersList == False):
                        raise Exception(f"Failed scrapping at {CategoryID} at {currentPrice} - {PriceTo}[{offset}]")
                    if available < 4000 and total == 0:
                        break
                    if (len(offersList) == 0):
                        while True:
                            if (offset < 0):
                                skip = True
                                break
                            offersList, available = self.retryOnFail(self.getOffers,f"Failed to get offers at {CategoryID} at price range {currentPrice} - {PriceTo}[{offset}]",reauth=True,double_return=True,CategoryID = CategoryID, offset = offset, PriceFrom=currentPrice, PriceTo=PriceTo)
                            if (offersList == False):
                                raise Exception(
                                    f"Failed scrapping at {CategoryID} at {currentPrice} - {PriceTo}[{offset}]")
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

                        print(f"Found {len(offersList) + offset} at price < {currentPrice} in {time.time() - start_time} s")

                        if((len(offersList) + offset)>1):
                            i +=1
                            entry = [{'Id': str(f"{CategoryID}x{offersList[len(offersList) - 1]['id']}"),
                                      'MessageBody': json.dumps({'id': str(CategoryID),
                                                                 "priceFrom": currentPrice,
                                                                 "priceTo": None, "apis": self.APICredentials,
                                                                 "proxies": self.proxies}),
                                      'MessageGroupId': str(random.randint(0, int(os.environ.get('MAX_CONCURRENCY')))),
                                      'MessageDeduplicationId':f"{CategoryID}x{str(currentPrice).replace('.','').replace(',','')}"}]
                            response = self.categoryQueue.send_messages(Entries=entry)
                        if((len(offersList) + offset)<5997):
                            break
                    else:
                        break
                print(f"Distributed {i} tasks in total.")

        if((time.time()-func_begin_time) <= int(os.environ.get('RESUME_THRESHOLD'))):
            joinedOfferList = []
            offset = 0
            for i in range(100):
                start_time = time.time()
                offersList = self.retryOnFail(self.getOffers,f"Failed to get offers at {CategoryID} at price range {PriceFrom} - {PriceTo}[{offset}]",reauth=True,double_return=True,CategoryID = CategoryID, offset = offset, PriceFrom=PriceFrom, PriceTo=PriceTo)
                if(offersList == False):
                    entry = [{'Id': str(f"RESUME-{CategoryID}"),
                              'MessageBody': json.dumps({'id': str(CategoryID),
                                                         "priceFrom": PriceFrom,
                                                         "priceTo": PriceTo,
                                                         "apis": self.APICredentials,
                                                         "proxies": self.proxies,
                                                         "resume": True}),
                              'MessageGroupId': str(random.randint(0, int(os.environ.get('MAX_CONCURRENCY')))),
                              'MessageDeduplicationId': f"RESUME-{CategoryID}x{str(PriceFrom).replace('.', '').replace(',', '')}"}]
                    response = self.categoryQueue.send_messages(Entries=entry)
                    break


                if (time.time() - start_time)>=2:
                    self.retryOnFail(self.auth, "Failed to Authenticate")

                if (len(offersList[0]) > 0):
                    joinedOfferList = joinedOfferList + offersList[0]
                else:
                    break
                offset += 60
            if (len(joinedOfferList) > 0):
                self.saveOffersToSQS(joinedOfferList, CategoryID)
            return {

                'statusCode': 200,
                'body': json.dumps(f'Done, {len(joinedOfferList)}')
            }
        else:
            print("Sent resume request")
            entry = [{'Id': str(f"RESUME-{CategoryID}"),
                      'MessageBody': json.dumps({'id': str(CategoryID),
                                                 "priceFrom": PriceFrom,
                                                 "priceTo": PriceTo,
                                                 "apis": self.APICredentials,
                                                 "proxies": self.proxies,
                                                 "resume": True}),
                      'MessageGroupId': str(random.randint(0, int(os.environ.get('MAX_CONCURRENCY')))),
                      'MessageDeduplicationId': f"RESUME-{CategoryID}x{str(PriceFrom).replace('.', '').replace(',', '')}"}]
            response = self.categoryQueue.send_messages(Entries=entry)


    def saveOffersToSQS(self, offers, CategoryID):
        start_time = time.time()
        dbQueue = random.choice(self.databaseQueues)
        dataChunk = int(os.environ.get('CHUNKS_IN_MESSAGE'))
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
                                'MessageGroupId': str(CategoryID),
                                'MessageDeduplicationId':self.generateDeduplicationToken()})
                messages += 1
                auctions = []
                c = 0

            if(len(entries) == maxEntries):
                self.retryOnFail(dbQueue.send_messages, 'Failed to send SQS message ', Entries=entries)

                entries = []

        if (len(auctions) != 0):
            entries.append({'Id': str(f"{CategoryID}-{messages}"),
                            'MessageBody': json.dumps({'id': str(CategoryID),
                                                       'data': auctions}),
                            'MessageGroupId': str(CategoryID),
                            'MessageDeduplicationId':self.generateDeduplicationToken()})

            messages += 1
        if (len(entries) != 0):

            self.retryOnFail(dbQueue.send_messages,'Failed to send SQS message ',Entries=entries)
        print(f'Result sent to DataBase Queue in {time.time() - start_time} s')

    def retryOnFail(self, callable, failMessage, reauth=False,double_return=False, *args, **kwargs):
        result = False
        result2 = 0
        try:
            self.setNewProxy()
            if(double_return):
                result,result2 = callable(*args, **kwargs)
            else:
                result = callable(*args,**kwargs)
        except Exception as e:
            retrySucceded = False
            for retry in range(self.maxRetries):
                time.sleep(self.retry_backoff_factor * (2 ** (retry) - 1))
                self.setNewProxy()
                try:
                    if (double_return):
                        result, result2 = callable(*args, **kwargs)
                    else:
                        result = callable(*args, **kwargs)
                    retrySucceded = True
                    break
                except Exception as e:
                    print(f'Failed retry: {failMessage} ({e}) {retry}/{self.maxRetries}')
                    if (reauth):
                        self.retryOnFail(self.auth, "Failed to Authenticate")
            if not retrySucceded:
                result = {
                    'statusCode': 429,
                    'body': json.dumps(f'{failMessage}')
                }

        return result,result2
