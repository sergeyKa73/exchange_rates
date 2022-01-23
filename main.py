import requests
import csv
import json

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
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Название валюты', 'Код', 'Курс', 'Кол-во'])
        for item in items:
            writer.writerow([item['Title'], item['Code'], item['OfficialRate'], item['Scale']])

# Сохраняем в xlsx
def dump_to_xlsx(items, path):
    if not len(items):
        return None
    pass


def main():
    res = get_content(get_html(URL))
    save_doc(res, CSV)


if __name__ =='__main__':
    main()