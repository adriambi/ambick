import requests
from bs4 import BeautifulSoup
import fake_useragent
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import re
import csv

USER = fake_useragent.UserAgent().random
HEADERS = {'user-agent': USER}
HOST = 'https://www.retail.ru'
URL = 'https://www.retail.ru/rbc/tradingnetworks/'
FILE = 'retailers.csv'


def get_html(url, params=None):
    """request html of the website with a list of retailers"""
    r = requests.get(url, headers=HEADERS, params=params)
    return r


def get_rubrics(html):
    """Scraping a dictionary of rubrics on the website "https://www.retail.ru/rbc/tradingnetworks/"

    :param html: requested html.text
    :return: {'54-ФЗ. Онлайн-кассы': 'https://www.retail.ru/rbc/tradingnetworks/businesses/54-fz/'}
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find(  # заменить это говнище на короткий xpath
        "div", class_="row default-list").find(
        "ul", class_="col-lg-6 col-md-6 col-sm-6 link-list").find_all("li") + soup.find(
        "div", class_="row default-list").find(
        "ul", class_="col-lg-6 col-md-6 col-sm-6 link-list").find_next(
        "ul", class_="col-lg-6 col-md-6 col-sm-6 link-list").find_all("li")

    rubrics = {}

    for item in items:
        rubrics[item.text.strip()] = HOST + item.find('a').get('href')
    return rubrics


def get_retailers(rubrics):
    """ The main function in this scraper. It starts from scraping a dictionary of rubrics (get_rubrics),
    then it counts the number of all retailers in rubric (get_pages_count), after that it gets the contacts of
    retailer in sequence

    :param rubrics: {'54-ФЗ. Онлайн-кассы': 'https://www.retail.ru/rbc/tradingnetworks/businesses/54-fz/', ...}
    :return:
    """
    for item in rubrics:
        retailers = []
        html_rubric = get_html(rubrics.get(item))
        if html_rubric.status_code == 200:
            pages_count = get_pages_count(html_rubric.text)
            for page in range(1, pages_count + 1):
                print(f'Парсинг страницы {page} из {pages_count}. Рубрика "{item}"...')  # inscription for user
                params_page = {"PAGEN_1": page} if page > 1 else None
                html_page = get_html(rubrics.get(item), params=params_page)
                retailers.extend(get_data(html_page.text, item))
        save_file(retailers)
    return retailers


def get_phone(url):
    """Getting the phone of the retailer using the Selenium to ShowPhone event.
    Options make the work of testing browser invisible.

    Example:
    :param url: https://www.retail.ru/rbc/tradingnetworks/7cont/
    :return str: (495) 933-43-63
    """
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options)

    driver.get(url)
    if driver.title == "Каталог торговых сетей":
        return "Error"
    check = driver.find_element_by_class_name("provider_detail")
    if re.search(r'\bПоказать телефон\b', check.text):
        btn_elem = driver.find_element_by_id("tel")
        try:
            btn_elem.click()
        except Exception:
            driver.close()
            return "Фото перекрыло доступ, проверить вручную"
        driver.close()
        return btn_elem.text
    else:
        driver.close()
        return "Не указан"


def get_data(html, dict_ret):
    """ Getting the dictionary full of retailers contacts from the website and its # of page

    :param html: requested (https://www.retail.ru/rbc/tradingnetworks/businesses/54-fz/).text
    :param dict_ret: '54-ФЗ. Онлайн-кассы'
    :return: [{'title': 'ГК Торгмонтаж', 'email': 'marketing@tm-ast.ru', 'phone': 'https://www.torgmontag.ru/',
    'actual': 'Информация актуальна на 12 мая 2020.'}]
    """
    soup = BeautifulSoup(html, 'html.parser')
    items = soup.find_all("div", class_="col")
    retailers_data = []
    for item in items:  # for each retailer
        data = {
            "category": dict_ret,
            "title": item.find("div", class_="title").get_text().strip()
        }
        retailer_data_url = HOST + item.find("a").get("href")  # finding its url on retail.ru
        req_ret_data = get_html(retailer_data_url)
        if req_ret_data.status_code == 200:
            soup = BeautifulSoup(req_ret_data.text, 'html.parser')
            data_soup = soup.find("div", class_="provider_detail")
            try:
                data["website"] = data_soup.find("div", class_="prop_item site").find("a").get_text().strip()
            except (AttributeError, KeyError):
                data["website"] = ""
            try:
                data["email"] = data_soup.find("a", class_="prop_item email").get_text().strip()
            except (AttributeError, KeyError):
                data["email"] = ""
            if retailer_data_url != URL:
                try:
                    data["phone"] = get_phone(retailer_data_url)
                except (AttributeError, KeyError):
                    data["phone"] = ""
            try:
                data["actual"] = data_soup.find("span", class_="info-actual").get_text().strip()
            except (AttributeError, KeyError):
                data["actual"] = ""
        retailers_data.append(data)
    return retailers_data


def get_pages_count(html):
    """ Getting the number of the last page of all retailers in this rubric (param html).

    :param html: requested (https://www.retail.ru/rbc/tradingnetworks/businesses/clothing-shoes-accessories/).text
    :return int: 4
    """
    soup = BeautifulSoup(html, 'html.parser')
    pagination_str = soup.find('ul', class_='pagination')
    if pagination_str:
        num = pagination_str.find_all("li")
        pages = num[-1].find('a').get('href').split("=")  # the last number is after "=" sign
        return int(pages[-1])
    else:
        return 1


def save_file(items, path=FILE):
    """Saving scrapped information about all retailers in 1 rubric into a retailers.csv"""
    with open(path, 'a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        list = ['category', 'title', 'website', 'email', 'phone', 'actual']
        for item in items:
            line = [item[name] for name in list]
            writer.writerow(line)


def parse():
    html = get_html(URL)
    if html.status_code == 200:
        with open(FILE, 'a', newline='') as file:
            writer = csv.writer(file, delimiter=';')
            writer.writerow(['Категория', 'Название', 'Сайт', 'E-mail', 'Телефон', 'Актуальность данных'])
        get_retailers(get_rubrics(html.text))


parse()
