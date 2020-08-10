import colorama
import json

class Category:
    def __init__(self):
        self.GREEN = colorama.Fore.GREEN
        self.GRAY = colorama.Fore.LIGHTBLACK_EX
        self.RESET = colorama.Fore.RESET
        self.RED = colorama.Fore.RED
        self.name = None
        self.offersNumber = None