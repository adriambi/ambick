import requests
from bs4 import BeautifulSoup
import csv

HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:80.0) Gecko/20100101 Firefox/80.0',
           'accept': '*/*'}
HOST = 'https://productcenter.ru'
FILE = 'manufactures.csv'


def get_html(url, params=None):
    """request html of the main page with a list of manufacturers"""
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_pages_count(html):
    """looking for and returning the number of manufacturer pages that need to be parsed"""
    soup = BeautifulSoup(html, 'html.parser')
    pagination = []
    pagination_str = soup.find('div', class_='page_links')
    if pagination_str:
        pagination_str = soup.find('div', class_='page_links').get_text().split()
        for item in pagination_str:
            if item == 'Вперёд':
                break
            else:
                pagination.append(int(item))
        return pagination[-1]
    else:
        return 1


def get_content(html):
    """
    get "Name" and "City" of the manufacturer, get data from get_contacts(), merge into a dictionary,
    return the combined dictionary with the keys: "Name", "City", "Site", "Phone", "Mail"
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='item firm vip') + soup.find_all('div', class_='item firm')

    producers = []
    for item in items:
        producers.append({
            'title': item.find('a', class_='link').get_text(),
            'city': item.find('span', class_='city').get_text()
        })
        html_contacts = get_html((HOST + item.find('a', class_='link').get('href')))  # get html of manufacture's link
        if html_contacts.status_code == 200:  # if there is some data
            contacts = get_contacts(html_contacts.text)  # going to the manufacturer's link and parse its contacts
            producers[-1].update(contacts)  # merging dictionaries

    return producers


def get_contacts(html):
    """dictionary with contact details of a certain manufacturer: "Site", "Phone", "Mail" """
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all('div', class_='bc_text')

    contacts = {}
    if items[-1].find('a', itemprop='url'):
        contacts['url'] = items[-1].find('a', itemprop='url').get_text()
    else:
        contacts['url'] = ' '

    if items[-1].find('span', itemprop='telephone'):
        contacts['phone'] = items[-1].find('span', itemprop='telephone').get_text()
    else:
        contacts['phone'] = ' '

    if items[-1].find('span', itemprop='email'):
        contacts['email'] = items[-1].find('span', itemprop='email').get_text()
    else:
        contacts['email'] = ' '

    return contacts


def parse():
    url = input('Введите url отрасли производителей с сайта productcenter.ru: ')
    html = get_html(url)
    if html.status_code == 200:
        producers = []
        pages_count = get_pages_count(html.text)  # looking for the number of pages to be parsed
        for page in range(1, pages_count + 1):  # for each page
            print(f'Парсинг страницы {page} из {pages_count}...')  # inscription for user
            html = get_html(url, params={'page': page})
            producers.extend(get_content(html.text))  # fill in the list with dictionaries, 1 dict. - 1 manufacturer
        save_file(producers, FILE)  # saving in csv file
        print(f'Получено {len(producers)} производителей')  # inscription for user about common quantity
    else:
        print('Error')


def save_file(items, path):
    """Saving scrapped information into a manufactures.csv"""
    with open(path, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Название', 'Город', 'Сайт', 'Телефон', 'Почта'])
        list = ['title', 'city', 'url', 'phone', 'email']
        for item in items:
            line = [item[name] for name in list]
            writer.writerow(line)


parse()
