from DBManager import DBManager
from AllegroApi import AllegroApi
from AllegroCategoryScrapper import CategoryAPIScrapper
import json
db = None

def Main(event,context=None):
    if __name__ == "__main__" or __name__ == "Main":
        print(event['Records'][0]['body'])
        try:
            data = json.loads(event['Records'][0]['body'])

        except:
            data = event['Records'][0]['body']
        allegro = AllegroApi(data['proxies'],data['apis'])
        allegro.auth()
        response = allegro.searchForOffersRecurrently(data['id'], data['priceFrom'], data['priceTo'])
        return response

def ScrapCategory(event = None,context=None):
    if __name__ == "__main__" or __name__ == "Main":
        print('Connecting to database....')
        db = DBManager(tunnel=False)
        print("Connected!")
        allegro = CategoryAPIScrapper(db)
        allegro.auth()
        response = allegro.getCategories()
        return response

#Main({"Records":[{"body":12}]})
#ScrapCategory()