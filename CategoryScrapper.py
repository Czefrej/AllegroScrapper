from bs4 import BeautifulSoup
import grequests
import requests
import time
import colorama
class CategoryScrapper:
    def __init__(self):
        self.offers = set()
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED

    def scrap(self,CategoryID):
        page = 1
        while True:
            link = f"https://allegro.pl/kategoria/{CategoryID}"
            if(page > 1):
                link = f"https://allegro.pl/kategoria/{CategoryID}?p={page}"
            reqs = requests.get(link,allow_redirects=False,headers={"User-Agent":"Mozilla/5.0"})
            if(reqs.status_code) == 301:
                page -=1
                print(f"{self.RED}[>] Found {page} pages of category {CategoryID}")
                break
            else:
                print(f"{self.GREEN}[{reqs.status_code}] Category link: {link}  {self.RESET}")

            soup = BeautifulSoup(reqs.text, 'lxml')

            page += 1
