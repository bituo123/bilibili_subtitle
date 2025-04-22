from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

class BilibiliCrawler:
    def __init__(self):
        self.driver = None
        self.logs = []
        self.videos = []  # 存储所有视频信息，每个元素是 {"alt": alt_name, "url": video_url}

    def log(self, message):
        """Print log message to console"""
        print(message)

    def crawl(self, uid):
        """Execute crawling logic"""
        try:
            # Initialize WebDriver
            options = webdriver.ChromeOptions()
            options.add_argument("--start-maximized")
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
            self.log("Browser started")

            # 1. Go to Bilibili homepage
            self.driver.get("https://www.bilibili.com/")
            self.log("Opened Bilibili homepage, please login...")

            # 2. Wait for manual login
            self.log("Please complete login in the browser, then press Enter in the console to continue...")
            input()
            self.log("Login detected, continuing...")

            # 3. Go to upload video page
            upload_url = f"https://space.bilibili.com/{uid}/upload/video"
            self.driver.get(upload_url)
            self.log(f"Navigated to upload video page: {upload_url}")
            time.sleep(5)

            # 4. Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#app > main > div.space-upload > div.upload-content"))
            )
            self.log("Page loaded, searching for elements...")

            # 5. Crawl all pages
            current_page = 1
            total_pages = 15  # 假设总共有15页
            
            while current_page <= total_pages:
                self.log(f"Processing page {current_page}/{total_pages}")
                
                # Find all video elements on current page
                elements = self.driver.find_elements(By.CSS_SELECTOR,
                    "#app > main > div.space-upload > div.upload-content > div > div.video-body > div > div > div > div > div > div > div.bili-video-card__cover > a > div.bili-cover-card__thumbnail > img")
                
                if not elements:
                    self.log("No matching elements found on this page")
                    break
                
                # Process each element
                for element in elements:
                    try:
                        alt_name = element.get_attribute("alt")
                        self.log(f"Processing video, alt attribute: {alt_name}")

                        # Get video URL
                        parent_a = element.find_element(By.XPATH, "./ancestor::a")
                        video_url = parent_a.get_attribute("href")
                        self.log(f"Video URL: {video_url}")

                        # Store as dictionary
                        self.videos.append({
                            "alt": alt_name,
                            "url": video_url
                        })

                    except Exception as e:
                        self.log(f"Error processing video: {str(e)}")
                        # Close tab if open and switch back
                        if len(self.driver.window_handles) > 1:
                            self.driver.close()
                            self.driver.switch_to.window(self.driver.window_handles[0])
                
                # Save data after each page
                
                
                # Check if we need to go to next page
                if current_page < total_pages:
                    try:
                        # Click next page button
                        next_page_btn = self.driver.find_element(By.CSS_SELECTOR,
                            "#app > main > div.space-upload > div.upload-content > div > div.video-footer > div > div.vui_pagenation--btns > button:nth-child(11)")
                        next_page_btn.click()
                        self.log("Clicked next page button")
                        
                        # Wait for page to load
                        time.sleep(3)
                        WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, "#app > main > div.space-upload > div.upload-content"))
                        )
                        
                        current_page += 1
                    except Exception as e:
                        self.log(f"Failed to go to next page: {str(e)}")
                        break
                else:
                    break


            self.save_data()

        except Exception as e:
            self.log(f"Error occurred: {str(e)}")
        finally:
            self.quit_browser()
            self.log("Crawling completed")

    def save_data(self):
        """Save collected video data to file"""
        try:
            # Save as JSON for structured data
            with open("bilibili/videos.json", "w", encoding="utf-8") as f:
                json.dump(self.videos, f, ensure_ascii=False, indent=2)
            
            # Also save as text file for URLs only
            with open("bilibili/videos.txt", "w", encoding="utf-8") as f:
                for video in self.videos:
                    f.write(f"{video['alt']}\t{video['url']}\n")
            
            self.log(f"Saved {len(self.videos)} videos to bilibili/videos.json and bilibili/videos.txt")
        except Exception as e:
            self.log(f"Failed to save data: {str(e)}")

    def quit_browser(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.log("Browser closed")

if __name__ == "__main__":
    uid = input("Enter UP 主 UID (default: 666759136): ").strip() or "666759136"
    if not uid.isdigit():
        print("Error: Please enter a valid UID (digits only)")
    else:
        crawler = BilibiliCrawler()
        crawler.crawl(uid)