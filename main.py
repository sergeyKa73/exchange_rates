import requests
import csv
import datetime
import sqlite3

now = datetime.datetime.now()
date = now.strftime("%d-%m-%Y %H:%M")

db_path = 'OfficialRate.db'
CSV = 'OfficialRate.csv'
URL = 'https://www.nbrb.by/api/exrates/rates?periodicity=0'
HEADERS = {
    'accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
}


def get_html(url, params=''):
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_content(html):
    data = []
    for el in html.json():
        s = list(el.values())[2::]
        data.append(
            {
                'Title': s[2],
                'Code': s[0],
                'OfficialRate': s[-1],
                'Scale': s[1],
            }
        )
    return data


# Сохраняем в файл csv
def save_doc(items, path):
    with open(path, 'a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Название валюты', 'Код', 'Курс', 'Кол-во', 'Дата'])
        for item in items:
            writer.writerow([item['Title'], item['Code'], item['OfficialRate'], item['Scale'], date])


def get_currencies(html):
    currency_dict = {}
    for el in html.json():
        for k, v in el.items():
            if v == "USD":
                currency_dict['USD'] = el['Cur_OfficialRate']
            elif v == "EUR":
                currency_dict['EUR'] = el['Cur_OfficialRate']
            elif v == "RUB":
                currency_dict['RUB'] = el['Cur_OfficialRate']
    return currency_dict


def print_data_2d(column_names, data):
    print(column_names)
    for line in data:
        print(line)
    print(F'number of lines in database table is: {len(data)}')


def write_current_db(cur_dict, path):  # создание db и запись в нее

    def count_records(table, cursor):  # поиск элементов в таблице db
        sql = F'SELECT COUNT(*) as count FROM {table}'
        cursor.execute(sql)
        id = cursor.fetchone()[0] + 1
        return id

    table = 'currencies'

    con = sqlite3.connect(path)
    cur = con.cursor()

    query = F'CREATE TABLE IF NOT EXISTS {table} (id, usd_rate, eur_rate, byn_rate, date)'
    cur.execute(query)
    con.commit()

    query = F'INSERT INTO {table} VALUES ({count_records(table, cur)},{cur_dict["USD"]},{cur_dict["EUR"]},{cur_dict["RUB"]},"{date}")'
    cur.execute(query)
    con.commit()
    con.close()


def sqlite_read_db(path, table, column_name=None):
    """
    функция чтения всех данных из базы данных
    """
    con = sqlite3.connect(path)
    cur = con.cursor()
    query_columns = 'PRAGMA table_info(' + table + ')'
    cur.execute(query_columns)
    column_descriptions = cur.fetchall()  # fetcone() - считывает одну запись
    column_names = []
    for column in column_descriptions:
        column_names.append(column[1])

    if column_name is None:
        query = F'SELECT * FROM {table}'
        cur.execute(query)
        data = cur.fetchall()  # Помещаем считанные записи из запроса в переменную data
    else:
        query = F'SELECT {column_name} FROM {table}'
        cur.execute(query)
        data = cur.fetchall()
        new_data = []
        for el in data:
            new_data.append(el[0])
        data = new_data
        del (new_data)

    cur.close()
    con.close()
    return print_data_2d(column_names, data)


def main():
    html = get_html(URL)
    res = get_content(html)
    save_doc(res, CSV)
    currency_dict = get_currencies(html)
    write_current_db(currency_dict, db_path)
    table = 'currencies'
    sqlite_read_db(db_path, table)


if __name__ == '__main__':
    main()
