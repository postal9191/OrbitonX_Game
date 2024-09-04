import sys
import requests
import json
import time
from datetime import datetime, timezone, timedelta
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import binascii
from concurrent.futures import ThreadPoolExecutor, as_completed

# Задаем ключ шифрования, аналогичный V7 в JavaScript (должен быть 16, 24 или 32 байта)
KEY = "kasdfrfsddf3234234123asdfghjkl12".encode('utf-8')


# Открываем файл и загружаем данные
with open('config.json', 'r', encoding='utf-8') as json_file:
    loaded_data = json.load(json_file)

# Функция для обновления времени авторизации в каждом наборе данных
def update_auth_date(auth_data):
    current_timestamp = int(time.time())
    auth_data['webAppInitData']['auth_date'] = str(current_timestamp)
    return auth_data

# Обновляем время авторизации для всех записей
loaded_data['authData'] = [update_auth_date(auth) for auth in loaded_data['authData']]

def token_regen(auth_data):
    url = "https://api.orbitonx.com/api/auth"
    payload = json.dumps(auth_data)
    headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'ru,en;q=0.9,en-GB;q=0.8,en-US;q=0.7',
        'authorization': 'Bearer null',
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
        'x-request-id': 'q9906',
        'x-timezone': 'Europe/Moscow'
    }

    response = requests.post(url, headers=headers, data=payload).json()
    token = response['data']['token']
    return token


def decrypt_token(encrypted_token):
    encrypted_data, iv_hex = encrypted_token.split(':')
    encrypted_bytes = base64.b64decode(encrypted_data)
    iv = binascii.unhexlify(iv_hex)
    cipher = AES.new(KEY, AES.MODE_CBC, iv)
    decrypted_data = unpad(cipher.decrypt(encrypted_bytes), AES.block_size)
    return decrypted_data.decode('utf-8')

def api_claim_get_coin(token):
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

    response = requests.patch(url, headers=headers)
    data = response.json()
    if data.get('statusCode') == 401 and data.get('message') == 'Unauthorized':
        print("Неавторизованный доступ. Завершение программы.")
        sys.exit(1)

    active_portfolios = [p for p in data["data"]["quest"]["portfolios"] if p["active"]]

    if active_portfolios:
        coins_ids = [coin["id"] for coin in active_portfolios[0]["coins"]]
        return coins_ids

    inactive_portfolios = [p for p in data["data"]["quest"]["portfolios"] if not p["active"]]

    if inactive_portfolios:
        finish_staking_dates = [p["finishStaking"] for p in inactive_portfolios]
        return finish_staking_dates
    return []

def api_coin_patch(token, coin_id):
    url = "https://api.orbitonx.com/api/user-coins"
    payload = json.dumps({
        "coins": [{"id": coin_id[i], "progress": 100} for i in range(min(5, len(coin_id)))],
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

    requests.patch(url, headers=headers, data=payload)

def is_date(value):
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False

def check_craft(response):
    if isinstance(response, list) and len(response) > 0 and is_date(response[0]):
        utc_time = datetime.fromisoformat(response[0].replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        wait_time = (utc_time - current_time).total_seconds() + 5 * 60

        if wait_time > 0:
            print(f"Следующий сбор в {utc_time.astimezone()}")
            time.sleep(wait_time)
            return True
    return False

def process_auth_data(auth_data):
    while True:
        try:
            encrypted_token = token_regen(auth_data)
            token = decrypt_token(encrypted_token)
            response = api_claim_get_coin(token)

            if check_craft(response):
                continue

            api_coin_patch(token, response)
            print(f"Следующий сбор в {datetime.now() + timedelta(hours=4, minutes=5)}")
            # time.sleep(3600 * 4 + 300)  # Ожидание 4 часа и 5 минут перед следующей итерацией
            break  # Завершить цикл при успешном выполнении
        except Exception as e:
            print(f"Ошибка обработки данных: {e}. Повтор через 1 минуту.")
            time.sleep(60)  # Ожидание 1 минуты перед повтором

# Использование ThreadPoolExecutor для параллельного выполнения
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(process_auth_data, auth) for auth in loaded_data['authData']]
    for future in as_completed(futures):
        try:
            future.result()  # Получаем результат выполнения
        except Exception as e:
            print(f"Ошибка выполнения задачи: {e}. Повтор через 1 минуту.")
            time.sleep(60)  # Ожидание 1 минуты перед повтором

print("Все задачи выполнены.")
