from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import streamlit as st
import requests
import os
import time
import re
import zipfile
from io import BytesIO

# Define the temporary folder for Streamlit session
TEMP_DIR = 'temp_images'

st.title('Google Image Scraper')

input_link = st.text_input("Enter your link")

if st.button("Scrape"):
    try:
        # Verify that the input link is valid by sending a request
        response = requests.get(input_link)
        if response.status_code == 200:
            st.write("Valid link, scraping data...")

          
            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--headless") 
            options.add_argument("--disable-gpu")  # Additional option for headless mode
            options.add_argument("--incognito") 
            driver = webdriver.Chrome(options=options)
            driver.get(input_link)

            try:
                # Locate the business name
                business_name = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.TIHn2 > div > div.lMbq3e > div:nth-child(1) > h1"))
                ).text

                # Finding and clicking the image button
                image_buttons = driver.find_elements(By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.ZKCDEc")
                if image_buttons:
                    image_buttons[0].click()  

                # Locate the scrollable container
                scroll = WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "#QA0Szd > div > div > div.w6VYqd > div.bJzME.tTVLSc > div > div.e07Vkf.kA9KIf > div > div > div.m6QErb.DxyBCb.kA9KIf.dS8AEf.XiKgde"))
                )

                # Function to scroll down
                def fast_scroll(driver, scroll_count):
                    for _ in range(scroll_count):
                        driver.execute_script("arguments[0].scrollTop += 2000;", scroll)
                        time.sleep(0.5)

                st.write("Getting all the images")
                fast_scroll(driver, 60)  
                st.write("All images found!")

                # Function to download images
                def download_image(folder_name, driver):
                    path = TEMP_DIR
                    img_folder = os.path.join(path, folder_name, "images-folder")
                    os.makedirs(img_folder, exist_ok=True)
                    
                    total_downloaded = 0  # counting images

                    try:
                        wait = WebDriverWait(driver, 10)
                        image_elements = wait.until(EC.presence_of_all_elements_located(
                            (By.CSS_SELECTOR, "div.Uf0tqf.loaded"))) 

                    except TimeoutException:
                        st.write("No images available")
                        return img_folder, total_downloaded

                    for index, img in enumerate(image_elements):
                        style_attribute = img.get_attribute("style")
                        img_url_match = re.search(r'url\("?(.+?)"?\)', style_attribute)

                        if img_url_match:
                            img_url = img_url_match.group(1).replace("\\", "")  # Clean the URL
                            try:
                                img_name = f"image_{index}.jpg"
                                img_data = requests.get(img_url).content
                                with open(os.path.join(img_folder, img_name), "wb") as f:
                                    f.write(img_data)
                                total_downloaded += 1  
                            except Exception as e:
                                st.write(f"Error downloading image {img_url}: {e}")
                    
                    return img_folder, total_downloaded

                # Create folder and download images
                folder_name = re.sub(r"[^\w\s]", "", business_name).lower().replace(" ", "_")
                image_folder, total_downloaded = download_image(folder_name, driver)

                # Show total downloads
                st.write(f"Total images downloaded: {total_downloaded}")

                # Zip the downloaded images
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for root, _, files in os.walk(image_folder):
                        for file in files:
                            zip_file.write(os.path.join(root, file), arcname=os.path.relpath(os.path.join(root, file), image_folder))

                st.write("Images downloaded and zipped!")

                # Flush the zip buffer
                zip_buffer.seek(0)

                # Download button for the ZIP file
                st.download_button(
                    label="Download Scraped Images",
                    data=zip_buffer,
                    file_name=f"{folder_name}.zip",
                    mime='application/zip'
                )

            except NoSuchElementException:
                st.error("Element not found on the page.")
            driver.quit()
        else:
            st.error("Invalid link or server not reachable.")
    except requests.exceptions.RequestException as e:
        st.error(f"Error accessing link: {e}")
