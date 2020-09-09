from DBManager import DBManager
from AllegroApi import AllegroApi
from AllegroCategoryScrapper import CategoryAPIScrapper
db = None

def Main(event,context=None):
    if __name__ == "__main__" or __name__ == "Main":
        print(event['Records'][0]['body'])
        print('Connecting to database....')
        db = DBManager()
        print("Connected!")
        allegro = AllegroApi(db)
        allegro.auth()
        response = allegro.getOffers(event['Records'][0]['body'])

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