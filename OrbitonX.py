import sys

import requests
import json
import time
from datetime import datetime, timezone, timedelta

# Открываем файл и загружаем данные
with open('config.json', 'r') as file:
    config = json.load(file)

# Извлекаем токен
token = config['token']

def api_claim_get_coin():
    url = "https://api.orbitonx.com/api/user-coins/collect-reward"

    headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
    'authorization': f'Bearer {token}',
    'origin': 'https://game.orbitonx.com',
    'priority': 'u=1, i',
    'referer': 'https://game.orbitonx.com/',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127", "Microsoft Edge WebView2";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
    'x-request-id': 'rbqnye',
    'x-timezone': 'Europe/Moscow'
    }

    response = requests.request("PATCH", url, headers=headers)
    data = response.json()
    print(data)
    if data.get('statusCode') == 401 and data.get('message') == 'Unauthorized':
        print("Неавторизованный доступ. Завершение программы.")
        sys.exit(1)

    # Проверка на активные портфели и получение ID монет
    active_portfolios = [p for p in data["data"]["quest"]["portfolios"] if p["active"]]

    if active_portfolios:
        coins_ids = [coin["id"] for coin in active_portfolios[0]["coins"]]
        return coins_ids

    # Если нет активных портфелей, возвращаем finishStaking для неактивных портфелей
    inactive_portfolios = [p for p in data["data"]["quest"]["portfolios"] if not p["active"]]

    if inactive_portfolios:
        finish_staking_dates = [p["finishStaking"] for p in inactive_portfolios]
        return finish_staking_dates
    return []



def api_coin_patch():
    coins_ids = api_claim_get_coin()

    url = "https://api.orbitonx.com/api/user-coins"
    payload = json.dumps({
        "coins": [
            {
                "id": coins_ids[0],
                "progress": 100
            },
            {
                "id": coins_ids[1],
                "progress": 100
            },
            {
                "id": coins_ids[2],
                "progress": 100
            },
            {
                "id": coins_ids[3],
                "progress": 100
            },
            {
                "id": coins_ids[4],
                "progress": 100
            }
        ],
        "energy": 0
    })
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'authorization': f'Bearer {token}',
        'content-type': 'application/json',
        'origin': 'https://game.orbitonx.com',
        'priority': 'u=1, i',
        'referer': 'https://game.orbitonx.com/',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Microsoft Edge";v="127", "Chromium";v="127", "Microsoft Edge WebView2";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36 Edg/127.0.0.0',
        'x-request-id': 'njv9dk',
        'x-timezone': 'Europe/Moscow'
    }

    response = requests.request("PATCH", url, headers=headers, data=payload)
    print(response)


def is_date(value):
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


while True:
    response = api_claim_get_coin()

    if isinstance(response, list) and len(response) > 0 and is_date(response[0]):
        utc_time = datetime.fromisoformat(response[0].replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)  # Приводим текущее время к UTC с временной зоной
        wait_time = (utc_time - current_time).total_seconds() + 5 * 60

        if wait_time > 0:
            print(f"Следующий сбор в {utc_time.astimezone()}")
            time.sleep(wait_time)
            continue  # Переход к началу нового цикла после ожидания
        else:
            print("Время уже прошло, переход к следующей итерации")

    # Если данных не было или они не дата, выполняем основной код
    api_coin_patch()
    print(f"Следующий сбор в {datetime.now() + timedelta(hours=4, minutes=5)}")
    time.sleep(3600 * 4 + 300)  # Ожидание 4 часа и 5 минут перед следующей итерацией