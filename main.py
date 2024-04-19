import os
import sys
import csv
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv, find_dotenv
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
_ = load_dotenv(find_dotenv())   

def reject_cookies() -> None:
    """Reject all cookies right after opening Instagram's page."""
    try:
        cookie_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'button[class="_a9-- _a9_1"]')))
        cookie_button.click()

        print("Successfully rejected cookies.")
    except Exception as e:
        print("Failed to reject cookies: ", str(e))

def reject_notifications() -> None:
    """Click on the button to reject turning on the notifications."""
    try:
        not_now = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
                (By.CSS_SELECTOR, 'button[class="_a9-- _a9_1"]')))
        not_now.click()

        print("Successfully rejected turning notifications on.")
    except Exception as e:
        print("Failed to reject turning notifications on.")

def login() -> None:
    """Login in Instagram using username and password from the .env file.
    TODO: create a condition, e.g. wait for a specific button to be available, 
    to show logged in successfully"""
    try:
        username = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[name="username"]')))
        password = WebDriverWait(driver, 10).until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, 'input[name="password"]')))

        username.clear()
        password.clear()

        username.send_keys(os.environ['INSTAGRAM_USERNAME'])
        time.sleep(1.5)
        password.send_keys(os.environ['INSTAGRAM_PASSWORD'])
        time.sleep(1.3)
        password.send_keys(Keys.RETURN)

        print("Successfully logged in.")
    except Exception as e:
        print("Failed to login: ", str(e))

def transform_datetime(datetime_str):
    dt = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%fZ')

    return dt.strftime('%Y-%m-%d')

def scrape_comment(url: str, scroll_down: bool=False) -> dict:
    """Return a list with all the comments from the given url.
    
    Args:
        url: The URL of the post.
        scroll_down: Load more comments

    Returns:
        A dictionary in which the key is a string of the user who posted and 
        the value is a list with the comments. 
    """

    driver.get(url)

    if scroll_down: 
        loaded_comment_pages = get_more_comments(n=100000, load_all=False)

    source = driver.page_source
    soup = BeautifulSoup(source, "html.parser")

    try:
        post_user = soup.find('a', class_="x1i10hfl xjbqb8w x6umtig x1b1mbwd xaqea5y xav7gou x9f619 x1ypdohk xt0psk2 xe8uvvx xdj266r x11i5rnm xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x16tdsg8 x1hl2dhg xggy1nq x1a2a7pz _acan _acao _acat _acaw _aj1- _a6hd").text
        post_date = soup.find('time', class_='_aaqe')['datetime']

        post_comments = list()
        outer_divs = soup.select('div._a9zr')

        for div in outer_divs:
            # Inside each outer div, find the inner div and extract the text of the span
            inner_div = div.select_one('div._a9zs')
            span = inner_div.select_one('span._aacl._aaco._aacu._aacx._aad7._aade')
            if span:
                comment = span.text
            else:
                comment = ''

            time_tag = div.select_one('time._a9ze._a9zf')
            if time_tag:
                comment_date = str(time_tag['datetime'])
            else:
                comment_date = ''
            
            if comment and comment_date:
                post_comments.append({
                    'comment_date': comment_date, 
                    'comment': comment
                })

        post_info = {
            'post_url': url, 
            'post_user': post_user, 
            'post_date': post_date, 
            'post_comments_pages': loaded_comment_pages,
            'post_comments': post_comments
        }

        print("Successfully scraped comments.")

        return post_info
    except Exception as e:
        print("Error scraping comments: ", e)
        return None

def get_more_comments(n: int=2, load_all: bool=False) -> int:
    """Click on the '+' symbol in the comment section to load more comments.
    
    Args:
        n: Load more comments 'n' times.
        load_all: It will load all comments.

    Raises:
        ValueError: The given n parameter is not greater than 0
    """
    full_xpath = '/html/body/div[2]/div/div/div[2]/div/div/div/div[1]/div[1] \
    /div[2]/section/main/div/div[1]/div/div[2]/div/div[2]/div/div/ul \
    /li/div/button'
    load_more_button = WebDriverWait(driver, 20).until(
        EC.element_to_be_clickable((By.XPATH, full_xpath)))

    if not driver.find_elements(By.XPATH, full_xpath):
        print("The 'load more comments' button is not available.")
        return

    if load_all:
        print("Loading all comments...")
        count = 0
        while True:
            time.sleep(1.5)
            if driver.find_elements(By.XPATH, full_xpath):
                load_more_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, full_xpath)))
                load_more_button.click()
                count += 1
                time.sleep(1.5)
            else:
                break
        print(f"Successfully finished loading all [{count}] comment pages.")
    else:
        if n <= 0:
            raise(ValueError("The parameter 'n' must be greater than 0."))
        
        print(f"Loading more comment pages...")
        for i in range(1, n + 1):
            try:
                time.sleep(1.5)
                if driver.find_elements(By.XPATH, full_xpath):
                    load_more_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, full_xpath)))
                    load_more_button.click()

                    if i > 9 and i % 10 == 0: 
                        print(f"Currently loaded [{i}] pages...")

                    time.sleep(0.5)
                else:
                    #print("Already loaded all comments."
                    #      "'Load more button' not found")
                    break
            except:
                print("Failed to load more comments \
                      or there wasn't enough comments")
                break
        print(f"Successfully loaded all [{i}] comment pages.")
    
        return i

def open_instagram_posts(filename: str) -> list:
    """Transform each post's code in a full instagram URL"""
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError as e:
        print("File not found: ", e)

    print("Successfully loaded all instagram posts.")

    return [line.strip() for line in lines if not line.startswith('#')]

def save_comments_in_json(new_data: dict, filename: str='data.json') -> None:
    print("Saving to [json] file...")
    if not os.path.exists(filename):
        with open(filename, 'w') as f:
            json.dump([], f)

    with open(filename, 'r+') as file:
        file_data = json.load(file)

        # if post doesnt exists, immediately appends it
        if not has_post(new_data, file_data):
            file_data.append(new_data)
            file.seek(0)
            json.dump(file_data, file, indent=4)
            print("Successfully saved new post to [json] file.")
        # if it exists, add only comments that are not there already
        else:
            print("Appending comments to existing post...")
            try:
                added_coments_count = 0
                for post in file_data:        
                    if post['post_url'] == new_data['post_url']:
                        for comment in new_data['post_comments']:
                            if comment not in post['post_comments']:
                                post['post_comments'].append(comment)
                                added_coments_count += 1
                        print(f"Successfully appended [{added_coments_count}] comments to [{post['post_url']}].")
                        break
                file.seek(0)
                json.dump(file_data, file, indent=4)
            except Exception as e:
                print("[save_comments_in_json] Error appending comment.", e)

def has_post(new_data: dict, file_data: json) -> bool:
    """Checks if a post is already in the json file."""
    for post in file_data:
        if post['post_url'] == new_data['post_url']:
            return True
    return False

def mark_link_as_visited(filename: str, link: str, loaded_comment_pages: int) -> None:
    # Read all lines from the file into a list
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Go through all lines and prepend "#" to the one that matches the link
    for i, line in enumerate(lines):
        # Strip newlines for comparison
        if line.strip() == link:
            lines[i] = f"#{lines[i].strip()};{str(loaded_comment_pages)}\n" 
            break  # Link only appears once, no need to continue searching

    # Write the lines back to the file
    with open(filename, 'w') as f:
        f.writelines(lines)
    
    print(f"Successfully marked [{link}] as read.")

def get_driver():
    user_data_dir = '/home/james/.config/google-chrome/Profile 2'
    chrome_options = Options()
    chrome_options.add_argument(user_data_dir)
    chrome_options.add_argument("--window-size=900x600")
    #chrome_options.add_argument("--headless=new")
    webdriver_service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=webdriver_service, 
                              options=chrome_options) 
    
    return driver

if __name__ == '__main__':
    driver = get_driver()
    driver.get("https://www.instagram.com/")

    reject_cookies()
    time.sleep(3)
    login()
    time.sleep(3)
    reject_notifications()
    time.sleep(3)

    instagram_posts = open_instagram_posts('instagram_posts.txt')
    base_url = "https://www.instagram.com/p/"

    if not instagram_posts:
        print("Error: the instagram_posts list is empty. Closing the program...")
        sys.exit()

    for idx, post in enumerate(start=1, iterable=instagram_posts):
        if not post:
            print("Skipping to the next post.")
            continue

        print(f"\n### Post: {post} - {idx}/{len(instagram_posts)} ###")
        time.sleep(1.5)
        full_url = base_url + post + '/'
        print("FULL URL:", full_url)

        try:
            start_time = time.time()
            comments = scrape_comment(full_url, True)

            if comments: 
                save_comments_in_json(comments)
                mark_link_as_visited('instagram_posts.txt', 
                                     post, comments['post_comments_pages'])                 
            else: 
                continue
            
            end_time = time.time()
            print(f"Time: ", end_time - start_time)

        except Exception as e:
            print("Error scraping comments in the MAIN: ", e)
