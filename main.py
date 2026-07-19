import requests
import csv
import datetime
import sqlite3
from fake_useragent import UserAgent
import urllib3

now = datetime.datetime.now()
date = now.strftime("%d-%m-%Y %H:%M")

db_path = 'OfficialRate.db'
CSV = 'OfficialRate.csv'
URL = 'https://www.nbrb.by/api/exrates/rates?periodicity=0'

user = UserAgent().random
HEADERS = {'user-agent': user}


def get_html(url, params=''):
    r = requests.get(url, headers=HEADERS, params=params, verify=False, timeout=10)
    return r


def get_content(html):
    data = []
    for el in html.json():
        if all(key in el for key in ['Cur_Name', 'Cur_Abbreviation', 'Cur_OfficialRate', 'Cur_Scale']):
            data.append(
                {
                    'Title': el['Cur_Name'],
                    'Code': el['Cur_Abbreviation'],
                    'OfficialRate': el['Cur_OfficialRate'],
                    'Scale': el['Cur_Scale'],
                }
            )
    return data


def save_doc(items, path):
    with open(path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Название валюты', 'Код', 'Курс', 'Кол-во', 'Дата'])
        for item in items:
            writer.writerow([item['Title'], item['Code'], item['OfficialRate'], item['Scale'], date])


def get_currencies(html):
    currency_dict = {}
    for el in html.json():
        if 'Cur_Abbreviation' in el and 'Cur_OfficialRate' in el:
            if el['Cur_Abbreviation'] == "USD":
                currency_dict['USD'] = el['Cur_OfficialRate']
            elif el['Cur_Abbreviation'] == "EUR":
                currency_dict['EUR'] = el['Cur_OfficialRate']
            elif el['Cur_Abbreviation'] == "RUB":
                currency_dict['RUB'] = el['Cur_OfficialRate']
    return currency_dict


def print_data_2d(column_names, data):
    # Способ 3: Краткий формат с выравниванием
    print("\n" + "="*80)
    print(f"{'ID':<5} {'USD Rate':<12} {'EUR Rate':<12} {'BYN Rate':<12} {'Date':<25}")
    print("="*80)
    for row in data:
        # Проверяем длину строки, чтобы избежать ошибок
        if len(row) >= 5:
            # Форматируем числа с 4 знаками после запятой
            usd = f"{row[1]:.4f}" if isinstance(row[1], (int, float)) else str(row[1])
            eur = f"{row[2]:.4f}" if isinstance(row[2], (int, float)) else str(row[2])
            byn = f"{row[3]:.4f}" if isinstance(row[3], (int, float)) else str(row[3])
            print(f"{row[0]:<5} {usd:<12} {eur:<12} {byn:<12} {row[4]:<25}")
    print("="*80)
    print(f'number of lines in database table is: {len(data)}')


def get_existing_columns(con, table):
    """Получить список существующих колонок в таблице"""
    cur = con.cursor()
    query = f'PRAGMA table_info({table})'
    cur.execute(query)
    columns = [col[1] for col in cur.fetchall()]
    cur.close()
    return columns


def write_current_db(cur_dict, path, table):
    con = sqlite3.connect(path)
    cur = con.cursor()

    # Проверяем существующие колонки
    existing_columns = get_existing_columns(con, table)

    # Если таблица существует, проверяем какие колонки есть
    if 'currencies' in [t[0] for t in con.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        # Если есть колонка rub_rate, используем её
        if 'rub_rate' in existing_columns:
            query = f'INSERT INTO {table}(usd_rate, eur_rate, rub_rate, date) VALUES (?, ?, ?, ?)'
            cur.execute(query, (cur_dict["USD"], cur_dict["EUR"], cur_dict["RUB"], date))
            con.commit()
            con.close()
            return
        # Если есть колонка byn_rate, используем её
        elif 'byn_rate' in existing_columns:
            query = f'INSERT INTO {table}(usd_rate, eur_rate, byn_rate, date) VALUES (?, ?, ?, ?)'
            cur.execute(query, (cur_dict["USD"], cur_dict["EUR"], cur_dict["RUB"], date))
            con.commit()
            con.close()
            return

    # Если таблицы нет, создаем новую с byn_rate
    query = f'CREATE TABLE IF NOT EXISTS {table} (id INTEGER PRIMARY KEY AUTOINCREMENT, usd_rate FLOAT, eur_rate FLOAT, byn_rate FLOAT, date TEXT)'
    cur.execute(query)
    con.commit()

    query = f'INSERT INTO {table}(usd_rate, eur_rate, byn_rate, date) VALUES (?, ?, ?, ?)'
    cur.execute(query, (cur_dict["USD"], cur_dict["EUR"], cur_dict["RUB"], date))
    con.commit()
    con.close()


def sqlite_read_db(path, table, column_name=None):
    """
    функция чтения всех данных из базы данных
    """
    con = sqlite3.connect(path)
    cur = con.cursor()

    # Получаем все колонки
    query_columns = f'PRAGMA table_info({table})'
    cur.execute(query_columns)
    column_descriptions = cur.fetchall()
    column_names = [column[1] for column in column_descriptions]

    if column_name is None:
        # Просто выводим все колонки как есть
        query = f'SELECT * FROM {table} ORDER BY id'
        cur.execute(query)
        data = cur.fetchall()
    else:
        if column_name not in column_names:
            print(f"Column '{column_name}' not found in table '{table}'")
            cur.close()
            con.close()
            return None

        query = f'SELECT {column_name} FROM {table} ORDER BY id'
        cur.execute(query)
        data = cur.fetchall()
        data = [el[0] for el in data]
        column_names = column_name

    cur.close()
    con.close()
    print_data_2d(column_names, data)
    return data


def main():
    table = 'currencies'
    html = get_html(URL)

    if html.status_code != 200:
        print(f"Error: Unable to fetch data. Status code: {html.status_code}")
        return

    res = get_content(html)
    save_doc(res, CSV)
    currency_dict = get_currencies(html)

    required_currencies = ['USD', 'EUR', 'RUB']
    missing = [c for c in required_currencies if c not in currency_dict]
    if missing:
        print(f"Warning: Missing currencies: {missing}")
        for currency in missing:
            currency_dict[currency] = 0.0

    write_current_db(currency_dict, db_path, table)


def read_db():
    table = 'currencies'
    sqlite_read_db(db_path, table)


if __name__ == '__main__':
    urllib3.disable_warnings()
    main()
    read_db()