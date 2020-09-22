from DBManager import DBManager
from AllegroApi import AllegroApi
from AllegroCategoryScrapper import CategoryAPIScrapper
import json
db = None
data = {
    "Records": [
        {
            "body": {
                "id": 90061,
                "priceFrom": 12.16,
                "priceTo": None,
                "apis": [
                    [
                        "d420364ce5a346778a67db3a03ec89ea",
                        "prBOWwMcwgvbveK4UkIONO16ROhmm5nYI3NYUxZ22ikSgoEoPtgODl8fhaI7nAkz"
                    ],
                    [
                        "dee90bdb76e045d18d88d0627ae53476",
                        "Iu5x4d6Wb2OgRQ3zeP5IYQBXoxg75Ty949xAnLTkzpnTXh2dysEfqASvt993iVOn"
                    ],
                    [
                        "44655b93fee04aefbf5e5fee457a5a85",
                        "kVBreDqGALrvvZqyxb2JQmjyDqr0rPRik9NvarDNFjgqUSKWUHPhZgsrdQTjh7GQ"
                    ],
                    [
                        "e4d5c0147a8e4610b18c169d00910757",
                        "TBR1CYVnnAWvmio1w7kkM15F8dRkNAQhJxdeu2YsmtdBEHdiLYwWfKrKgscw8CoE"
                    ],
                    [
                        "cb9ab87b4717420e97ee1a2d57cdee4f",
                        "24pIubQ0dmLpSq1QXkayOKi6O5ks6zzaFk1FJl35CgrOBXbsO59Ed6nWmEHpSRjv"
                    ]
                ],
                "proxies": [
                    [
                        "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.87:80"
                    ],
                    [
                        "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.244:80"
                    ],
                    [
                        "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.178:80"
                    ],
                    [
                        "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.81:80"
                    ],
                    [
                        "http://ypeokuao-1:9ui94tr5b0ac@2.56.101.132:80"
                    ]
                ]
            }
        }
    ]
}
def Main(event,context=None):
    if __name__ == "__main__" or __name__ == "Main":
        try:
            data = json.loads(event['Records'][0]['body'])

        except:
            data = event['Records'][0]['body']
        allegro = AllegroApi(data['proxies'],data['apis'])
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


Main(data)
#ScrapCategory()