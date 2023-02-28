import os
from dotenv import load_dotenv
import pyotp
import requests
import json
from datetime import datetime
import time

load_dotenv()
requests.packages.urllib3.disable_warnings()
chat_id = "-782003447"
api_key = os.getenv("TELEGRAM_BOT")

notified_ids = []

class bitskinsTools:
    def __init__(self):
        self.api_key = os.getenv("API_KEY")
        self.api_secret = os.getenv("API_SECRET")
        self.api_endpoint = "https://bitskins.com"

    def get2faCode(self):
        my_token = pyotp.TOTP(self.api_secret)
        return my_token.now()

    def getBalance(self):
        endpoint = "/api/v1/get_account_balance"
        url = self.api_endpoint + endpoint + "/?api_key=" + self.api_key + "&code=" + self.get2faCode()
        balance = requests.get(url)

        return balance.json()['data']['available_balance']

    def getSpecificItemOnSale(self, item_id):
        endpoint = "/api/v1/get_specific_items_on_sale"
        url = self.api_endpoint + endpoint + "/?api_key=" + self.api_key + "&code=" + self.get2faCode() + "&item_ids=" + item_id
        market_data = requests.get(url)

        data = market_data.json()
        for item in data['data']['items_on_sale']:
            print(item)
        
        print()

    def getLowPriceItem(self, item_market_hash):
        endpoint = "/api/v1/get_inventory_on_sale"
        url = self.api_endpoint + endpoint + "/?api_key=" + self.api_key + "&code=" + self.get2faCode() + "&per_page=480" + "&sort_by=price&order=asc" + "&market_hash_name=" + item_market_hash
        market_data = requests.get(url)
        if (market_data.status_code != 200):
            print(market_data.text)
            print(f"Error getting market data: {market_data.status_code}")
            return 0

        if (len(market_data.json()['data']['items']) == 0):
            print("no items found")
            return 0

        data = market_data.json()

        item_low_price = data['data']['items'][0]['price']

        return float(item_low_price)
    
    def buyItem(self, item_id, price):
        endpoint = "/api/v1/buy_item"
        url = self.api_endpoint + endpoint + "/?api_key=" + self.api_key + "&code=" + self.get2faCode() + "&item_ids=" + item_id + "&prices=" + str(price)

        balance = self.getBalance()
        if (balance < price):
            print("not enough money")
            return False
        if (price > 100):
            print("too expensive")
            return False
        if (price < 15):
            print("too cheap")
            return False

        buy = requests.get(url)
        if (buy.status_code != 200):
            print(buy.text)
            print(f"Error getting market data: {buy.status_code}")
            return False
        
        return True
        


    def checkSkinErrorPrice(self):
        endpoint = "/api/v1/get_inventory_on_sale"
        url = self.api_endpoint + endpoint + "/?api_key=" + self.api_key + "&code=" + self.get2faCode() + "&per_page=30" + "&sort_by=created_at&sort_order=asc"
        market_data = requests.get(url)
        if (market_data.status_code != 200):
            print(market_data.text)
            print(f"Error getting market data: {market_data.status_code}")

        if (len(market_data.json()['data']['items']) == 0):
            print("no items found")

        data = market_data.json()

        for item in data['data']['items']:

            lower = self.getLowPriceItem(item['market_hash_name'])
            if (lower == 0):
                continue

            date = datetime.fromtimestamp(item['updated_at']).strftime('%Y-%m-%d %H:%M:%S')
            item_id = item['item_id']
            price = float(item['price'])

            if (item['suggested_price'] == None):
                continue
            if (float(item['suggested_price']) <= 10):
                continue

            categorie = item['market_hash_name'].split("|")[0].strip()
            if (categorie == "Sticker"):
                continue
    
            discount = (lower - price) / lower * 100

            if (item_id not in notified_ids and discount > 10):
                message = "New interesting items found:\n\n"
                url = "https://bitskins.com/view_item?app_id=730&item_id=" + str(item_id)
                notified_ids.append(item_id)
                message += f"item:\t{item['market_hash_name']}\n"
                message += f"price:\t{price:.2f}€\n"
                message += f"discount:\t{discount:.2f}%\n"
                message += f"last update:\t{date}\n"
                message += f"url:\t{url}\n"
                message += "\n"
                send_telegram_message(message, chat_id, api_key)
                buyed = self.buyItem(item_id, price)

                if (buyed):
                    message = "Item bought:\n\n"
                    message += f"item:\t{item['market_hash_name']}\n"
                    message += f"price:\t{price:.2f}€\n"
                    message += f"discount:\t{discount:.2f}%\n"
                    message += f"last update:\t{date}\n"
                    message += f"url:\t{url}\n"
                    message += "\n"
                    send_telegram_message(message, chat_id, api_key)
                    print("item bought")

        return 0

def send_telegram_message(message: str, chat_id: str, api_key: str):
    headers = {'Content-Type': 'application/json'}
    data_dict = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML', 'disable_notification': True, 'disable_web_page_preview': True}
    data = json.dumps(data_dict)
    url = f'https://api.telegram.org/bot{api_key}/sendMessage'
    response = requests.post(url, data=data, headers=headers, verify=False)
    if response.status_code != 200:
        print(response.text)
        print(f"Error sending message to Telegram: {response.status_code}")

def main():
    bitskins = bitskinsTools()
    while True:
        try:
            bitskins.checkSkinErrorPrice()
        except Exception as e:
            print(e)

if __name__ == "__main__":
    print("Starting Bitskins bot...")
    main()
