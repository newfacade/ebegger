import json
import logging
import random
import time
from typing import List
import yaml

import undetected_chromedriver as uc
from jsonpath_ng import parse
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


def open_browser(
        profileDirectory: str,
        metaMaskDir: str,
        userDataDir: str,
):
    """
    :param profileDirectory: different profile directories for different users
    :param metaMaskDir:
        the directory of the MetaMask unzipped dir
        because we use undetected_chromedriver,we should use zip format
        ref: https://stackoverflow.com/questions/74934963/undetected-chromedriver-add-a-plugin
    :param userDataDir: all your user data will be stored in this directory
    :return:
    """
    option = uc.ChromeOptions()
    option.add_argument(f'--load-extension={metaMaskDir}')
    option.add_argument(f'--profile-directory={profileDirectory}')
    option.add_argument('--disable-features=PrivacySandboxAdsAPIs')
    option.add_argument(f'--user-data-dir={userDataDir}')
    driver = uc.Chrome(use_subprocess=True, options=option)
    return driver


def recovery_from_words(
        driver: webdriver.Chrome,
        words: List[str],
        localPassword: str,
        extension_id: str,
):
    driver.get(f"chrome-extension://{extension_id}/home.html#onboarding/welcome")

    WebDriverWait(driver, 10).until(EC.presence_of_element_located(
        (By.ID, "onboarding__terms-checkbox")
    )).click()  # click the first agree button

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/ul/li[3]/button')
    )).click()  # click the second agree button

    WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
        (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div/button[1]')
    )).click()  # wait for the recovery page to load

    for i in range(len(words)):  # input the recovery words
        input_element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (By.ID, f'import-srp__srp-word-{i}'),
            ))
        input_element.send_keys(words[i])

    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div[4]/div/button'),
        ),
    ).click()  # click the confirm button

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div[2]/form/div[1]/label/input'),
        )
    ).send_keys(localPassword)  # input the local password

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div[2]/form/div[2]/label/input'),
        ),
    ).send_keys(localPassword)  # confirm the local password

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div[2]/form/div[3]/label/input'),
        )
    ).click()  # understand the risk
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="app-content"]/div/div[2]/div/div/div/div[2]/form/button'),
        )
    ).click()  # click the import button


def load_recover_words_from_config(configFile: str):
    with open(configFile) as f:
        y = yaml.safe_load(f)
        return y["recover_words"].split(" ")


def login_to_nfprompt(driver: webdriver.Chrome, localPassword: str):
    driver.get("https://nfprompt.io/earn")
    driver.switch_to.window(driver.current_window_handle)
    WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable(
            (By.XPATH, '//*[@id="__nuxt"]/div[2]/div[2]/div/div[2]/div[1]/div[2]/button'),
        )
    ).click()  # click login

    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[3]/div/div[2]/div/div[2]/div/div/div/div[1]'),
        )
    ).click()
    # do not know why we can not use python code to click the button
    # so we use js code to click the button
    time.sleep(2)
    driver.execute_script(
        'document.querySelector("body > w3m-modal").shadowRoot.querySelector("#w3m-modal > div > div > w3m-modal-router").shadowRoot.querySelector("div > div > w3m-connect-wallet-view").shadowRoot.querySelector("w3m-desktop-wallet-selection").shadowRoot.querySelector("w3m-modal-footer > div.w3m-grid > w3m-wallet-button:nth-child(1)").shadowRoot.querySelector("button").click()')


def clean_all_other_windows(driver: webdriver.Chrome):
    """
    close all other windows except the current window
    :param driver:
    :return:
    """
    current = driver.current_window_handle
    for handle in driver.window_handles:
        if handle != driver.current_window_handle:
            driver.switch_to.window(handle)
            driver.close()
    driver.switch_to.window(current)


def get_meta_mask_extension_id(driver: webdriver.Chrome):
    driver.get("chrome://extensions")
    root_dict = driver.execute_cdp_cmd("DOM.getDocument", {"depth": -1, "pierce": True})
    extensions_expr = parse(
        "root.children[1].children[1].children[0].shadowRoots[0].children[10].children[2].children[0].shadowRoots[0].children[6].children[1].children[3].children")
    match = extensions_expr.find(root_dict)
    mv = match[0].value
    nodeValue_expr = parse(
        "shadowRoots[0].children[9].children[0].children[3].children[0].children[0].children[0].children[0].nodeValue")
    for m in mv:
        attributes = m["attributes"]
        if len(attributes) == 2 and attributes[0] == "id":
            inner_m = nodeValue_expr.find(m)
            if inner_m and inner_m[0].value == "MetaMask":
                return attributes[1]

    raise Exception("MetaMask extension id not found")


def main():
    localPassword = "!1234567890a"  # password for current browser login
    profileDirectory = "default" + str(random.randint(0, 999999))
    # profileDirectory = "default679221111"
    userDataDir = "userDataDir"  # all your user data will be stored in this directory

    driver = open_browser(
        profileDirectory=profileDirectory,
        metaMaskDir="MetaMask",
        userDataDir=userDataDir,
    )
    time.sleep(2)  # sleep for all default windows to open

    clean_all_other_windows(driver)
    # when we open browser , we may get two windows
    # one is default window, the other is the MetaMask window(if we first open the browser)
    # so we should close the metamask window
    # and check if the metamask has login
    extension_id = get_meta_mask_extension_id(driver)

    recovery_from_words(
        driver,
        words=load_recover_words_from_config("config.yaml"),
        localPassword=localPassword,
        extension_id=extension_id,
    )

    login_to_nfprompt(driver=driver, localPassword=localPassword)

    return driver


if __name__ == '__main__':
    d = main()
    time.sleep(99999)  # sleep for to stop the browser close
