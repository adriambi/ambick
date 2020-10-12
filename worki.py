from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import pickle
import time
import pyperclip

HOST = "https://hr.worki.ru"
AUTH = "https://worki.ru/hr/login?hr_cabinet_return_url=/"
CANDIDATES = "/applications"


def message_from_me(write_button):
    """If we have already sent a message, it means that this candidate is not new, and we don't need him/her

    :return: 1 if not new
    :return: 0 if new
    """
    write_button.click()
    wait = WebDriverWait(driver, 300)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//div[contains(@class, 'chatMessage_fromCandidate')]")))
    result = 1 if driver.find_elements_by_xpath("//div[contains(@class, 'chatMessage_mine')]") else 0
    chat_close = driver.find_element_by_xpath("//div[contains(@class, 'close_withoutOffset')]")
    chat_close.click()
    time.sleep(1)  # yes, it is necessary
    return result


def delete_candidate(candidate):
    """This function marks the candidate as 'Not suits', changes his/her status

    :param candidate: current webpage (candidate's worki.ru webpage)
    """
    status_button = candidate.find_element_by_xpath("//button[contains(@class, 'changeStatusButton')]")
    status_button.click()
    time.sleep(1)
    delete_button = candidate.find_element_by_xpath("//div[contains(@class, 'applicationStatusAction_improper')]")
    delete_button.click()


def write_candidate(candidate_webpage, file: str):
    """This function writes the candidate that his/her application is viewed,
    information is sent in WhatsApp (optionally).

    :param candidate_webpage: current webpage (candidate's worki.ru webpage)
    :param file: path to the file with the message
    """
    wait = WebDriverWait(driver, 300)
    wait.until(EC.visibility_of_element_located((By.XPATH, "//span[text()='Написать']/ancestor::button")))
    write_button = candidate_webpage.find_element_by_xpath("//span[text()='Написать']/ancestor::button")
    write_button.click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//textarea[@placeholder='Ваше сообщение']")))
    textarea = candidate_webpage.find_element_by_xpath("//textarea[@placeholder='Ваше сообщение']")
    textarea.click()
    message = open(file, "r").read().encode("cp1251").decode("utf-8")
    pyperclip.copy(message)
    textarea.send_keys(Keys.CONTROL + "v")
    candidate_webpage.find_element_by_xpath("//span[text()='Отправить']/parent::span").click()  # send message
    candidate_webpage.find_element_by_xpath("//div[contains(@class, 'close_withoutOffset')]").click()  # close the chat
    time.sleep(1)  # yes, it is necessary too


def change_status(candidate_webpage, status: str):
    """This function changes the status of chosen candidate depending on an ability of sending him/her
    information via WhatsApp. If it was sent successfully, than we invite the candidate, else we change the status as
    reserved

    :param candidate_webpage: current webpage
    :param status: what status should we choose
    """
    wait = WebDriverWait(candidate_webpage, 300)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'changeStatusButton')]")))
    candidate_webpage.find_element_by_xpath("//button[contains(@class, 'changeStatusButton')]").click()
    wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(@class, 'StatusAction')]")))
    if status == "StatusAction_invited":
        candidate_webpage.find_element_by_xpath("//div[contains(@class, 'StatusAction_invited')]").click()
    elif status == "StatusAction_reserved":
        candidate_webpage.find_element_by_xpath("//div[contains(@class, 'StatusAction_reserved')]").click()
    else:
        candidate_webpage.find_element_by_xpath("//div[contains(@class, 'StatusAction_improper')]").click()


def whatsapp(candidate, url: str):
    """In this function we are looking for the candidate's phone, writing him/her via WhatsApp and going to the
    candidate's webpage at the worki.ru.
    If message is sent successfully return 1, else 0.

    :param candidate: part of webpage
    :param url: candidate's webpage url on worki.ru
    :return: 1 or 0
    """
    wait = WebDriverWait(candidate, 300)  # sometimes WA works too slowly, we will wait 90 seconds max

    wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'button_white___346Oh')]")))
    candidate.find_element_by_xpath("//button[contains(@class, 'button_white___346Oh')]").click()
    wait.until(EC.visibility_of_element_located((
        By.XPATH, "//div[contains(@class, 'applicationStatusAction') and contains(text(), '+')]")))
    # time.sleep(2)  # yes, it is necessary
    phone = candidate.find_element_by_xpath("//div[contains(@class, 'applicationStatusAction')]").text
    num = [char for char in phone if char not in ["+", "(", ")", " "]]
    if num[0] == "8":
        num[0] = "7"
    phone = "".join(num)  # phone with the numbers from 0 to 9 only
    wa_url = "https://api.whatsapp.com/send?phone=" + phone

    driver.set_page_load_timeout(5)  # if we won't set some seconds, we will wait forever this webpage (only this)
    # noinspection PyBroadException
    try:
        driver.get(wa_url)
    except BaseException:
        pass
    driver.set_page_load_timeout(300)
    go_to_chat_button = wait.until(EC.visibility_of_element_located((By.ID, "action-button")))
    go_to_chat_button.click()
    driver.find_element_by_xpath("//a[contains(text(), 'используйте WhatsApp Web')]").click()

    time.sleep(2)
    auth_is_needed = driver.find_elements_by_xpath("//div[text()='Чтобы использовать WhatsApp на вашем компьютере:']")
    need_auth = True if auth_is_needed else False
    if need_auth:  # verification by QR-code
        print("Отсканируйте QR-код, дождитесь загрузки страницы и нажмите Enter.")
        input()
        print("Спасибо.")

    wait.until(EC.visibility_of_element_located((By.XPATH, "//div[text()='Поиск или новый чат']")))
    time.sleep(1)  # yes, it is necessary
    if driver.find_elements_by_xpath("//div[text()='Введите сообщение']/following-sibling::div"):
        wait.until(EC.element_to_be_clickable((By.XPATH, "//div[text()='Введите сообщение']/following-sibling::div")))
        textarea = driver.find_element_by_xpath("//div[text()='Введите сообщение']/following-sibling::div")
        time.sleep(4)
        textarea.click()
        message = open("worki_hello.txt", "r").read().encode("cp1251").decode("utf-8")
        pyperclip.copy(message)
        textarea.send_keys(Keys.CONTROL + 'v')
        textarea.send_keys(Keys.ENTER)
        driver.get(url)
        return 1
    elif driver.find_elements_by_xpath("//div[text()='Неверный номер телефона.']"):
        driver.get(url)
        return 0
    else:
        print("Unknown WhatsApp error.")


def find_unviewed_application(webpage):
    """This function looks for unviewed applications and returns the first found

    :param webpage: webpage (list of applications)
    :return: link for the candidate's webpage
    """
    wait = WebDriverWait(webpage, 300)
    wait.until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'initialLoading_hidden')]")))

    # case when there are no candidates
    if webpage.find_elements_by_xpath("//div[contains(@class, 'applications__emptyList')]"):
        return None

    user_not_found = True
    candidate_url = ""

    while user_not_found:
        # candidate_check = webpage.find_elements(By.CLASS_NAME, "application__application__3SboS")  # for all
        candidate_check = webpage.find_elements(By.XPATH, "//div[contains(@class, 'application_unread')]")  # for unread
        if candidate_check:
            candidate_url = candidate_check[0].find_elements_by_class_name("application__application__link__3c5EP")
            if candidate_url:
                candidate_url = candidate_check[0].find_element(
                    By.CLASS_NAME, "application__application__link__3c5EP").get_attribute("href")
            else:
                print("Требуется вмешательство! Сделайте этого кандидата просмотренным вручную и нажмите Enter")
                input()
                print("Спасибо.")
                sort_candidates(False)
            user_not_found = False
        elif not webpage.find_elements_by_xpath("//div[contains(@class, 'loadMoreResultsSpinner')]"):
            return None
        else:
            margin_top = webpage.find_element_by_xpath(
                "//div[contains(@class, 'initialLoading_hidden')]").get_attribute("style")
            while margin_top == webpage.find_element_by_xpath(
                    "//div[contains(@class, 'initialLoading_hidden')]").get_attribute("style"):
                webpage.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                if not webpage.find_elements_by_xpath("//div[contains(@class, 'loadMoreResultsSpinner')]"):
                    break
                time.sleep(1)
    return candidate_url


def sort_candidates(finish):
    """This function decides what should do with the first candidate from application list.
    If this candidate is underaged, program changes his/her status on "not suits", it means deletion.
    If the candidate has already been seen, it means that the application isn't new, so we delete him/her.
    Else we write the candidate via WhatsApp and invite him or make him/her reserved

    :return: "Отклики закончились." when all applications are over.
    """
    if finish:
        return True
    wait = WebDriverWait(driver, 300)
    driver.get(HOST + CANDIDATES)

    if find_unviewed_application(driver) is None:
        return True
    else:
        candidate_url = find_unviewed_application(driver)

    driver.get(candidate_url)
    wait.until(EC.element_to_be_clickable((By.XPATH, "//span[text()='Написать']/ancestor::button")))
    write_button = driver.find_element_by_xpath("//span[text()='Написать']/ancestor::button")
    age = driver.find_element_by_xpath("//div[text()='Возраст']/following-sibling::div").text.split()
    age = int(age[0])

    if age < 18:
        change_status(driver, "StatusAction_improper")
    elif not message_from_me(write_button):
        if whatsapp(driver, candidate_url):
            write_candidate(driver, "worki_invitation.txt")
            change_status(driver, "StatusAction_invited")
        else:
            write_candidate(driver, "worki_hello.txt")
            change_status(driver, "StatusAction_reserved")
    else:
        change_status(driver, "StatusAction_improper")
    sort_candidates(finish)


def auth(numbers: str):
    """If there is no cookies for a user, this function asks for verification and writes cookies. Else read cookies.
    :param numbers: 5550 (the last 4 numbers of user account phone
    """
    driver.get(AUTH)
    try:
        for cookie in pickle.load(open('session' + numbers, 'rb')):
            if cookie['domain'] == '.worki.ru':
                driver.add_cookie(cookie)
    except FileNotFoundError:
        print("Пройдите авторизацию и нажмите Enter.")
        input()
        print("Если вы всё сделали правильно, то авторизация пройдена.")
        pickle.dump(driver.get_cookies(), open('session' + numbers, 'wb'))


driver = webdriver.Firefox()
user = input('Выберите аккаунт для работы в Worki: "5550" или "3920". Введите последние 4 цифры и нажмите Enter: ')
print("Запрос принят.")
auth(user)
sort_candidates(False)
print("Отклики закончились.")
driver.close()


