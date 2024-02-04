import json
import time
from typing import List
import yaml

from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC


def open_browser_and_recovery_from_words(
        profileDirectory: str,
        metaMaskCRXFile: str,
        words: List[str],
        localPassword: str,
):
    option = webdriver.ChromeOptions()
    option.add_extension(metaMaskCRXFile)
    option.add_argument(f'--profile-directory={profileDirectory}')
    driver = webdriver.Chrome(options=option)
    while True:  # sleep for 0.5 seconds until extension webpages are loaded
        time.sleep(0.5)
        if len(driver.window_handles) == 2:
            driver.switch_to.window(driver.window_handles[-1])  # and switch to the extension window
            break

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

    time.sleep(100)  # just sleep for 100 seconds to keep the browser open


def load_recover_words_from_config(configFile: str):
    with open(configFile) as f:
        y = yaml.safe_load(f)
        return y["recover_words"].split(" ")


def main():
    localPassword = "!1234567890a"  # password for current browser login
    profileDirectory = "Default"  # different profile directories for different users
    open_browser_and_recovery_from_words(
        profileDirectory=profileDirectory,
        metaMaskCRXFile="MetaMask.crx",  # metaMask extension file(you should get it by yourself 🙂)
        words=load_recover_words_from_config("config.yaml"),
        localPassword=localPassword,
    )


if __name__ == '__main__':
    main()
