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
        self.ai_subtitle_urls = []

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

            # 5. Find all video elements
            elements = self.driver.find_elements(By.CSS_SELECTOR,
                "#app > main > div.space-upload > div.upload-content > div > div.video-body > div > div:nth-child(1) > div > div > div > div > div.bili-video-card__cover > a > div.bili-cover-card__thumbnail > img")
            
            if not elements:
                self.log("No matching elements found")
                return

            # 6. Process each element
            for i, element in enumerate(elements, 1):
                try:
                    alt_name = element.get_attribute("alt")
                    self.log(f"Processing video {i}, alt attribute: {alt_name}")

                    # Get video URL
                    parent_a = element.find_element(By.XPATH, "./ancestor::a")
                    video_url = parent_a.get_attribute("href")
                    self.log(f"Video URL: {video_url}")

                    # Open video in new tab
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get(video_url)
                    self.log("Opened video page")

                    # Open subtitles
                    self.open_subtitle()

                    # Search for ai_subtitle
                    self.search_ai_subtitle()

                    # Close the current tab and switch back to main tab
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    self.log("Closed video tab")

                except Exception as e:
                    self.log(f"Error processing video {i}: {str(e)}")
                    # Close tab if open and switch back
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

            # Save collected URLs
            self.save_urls()

        except Exception as e:
            self.log(f"Error occurred: {str(e)}")
        finally:
            self.quit_browser()
            self.log("Crawling completed")

    def open_subtitle(self):
        """Open subtitle for current video"""
        if not self.driver:
            self.log("Browser not running")
            return

        try:
            # Find player div and set data-ctrl-hidden to false
            player_div = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#bilibili-player > div > div"))
            )
            self.driver.execute_script("arguments[0].setAttribute('data-ctrl-hidden', 'false')", player_div)
            self.log("Set data-ctrl-hidden to false")

            # Click subtitle button
            subtitle_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR,
                    "#bilibili-player > div > div > div.bpx-player-primary-area > div.bpx-player-video-area > div.bpx-player-control-wrap > div.bpx-player-control-entity > div.bpx-player-control-bottom > div.bpx-player-control-bottom-right > div.bpx-player-ctrl-btn.bpx-player-ctrl-subtitle"))
            )
            subtitle_button.click()
            self.log("Clicked subtitle button")
        except Exception as e:
            self.log(f"Failed to open subtitle: {str(e)}")

    def search_ai_subtitle(self):
        """Search for ai_subtitle network requests"""
        if not self.driver:
            self.log("Browser not running")
            return

        try:
            # Get performance logs
            logs = self.driver.get_log("performance")
            self.logs.extend(logs)
            for entry in logs:
                log = json.loads(entry["message"])["message"]
                if "params" in log and "response" in log["params"] and "url" in log["params"]["response"]:
                    url = log["params"]["response"]["url"]
                    if "aisubtitle" in url and url not in self.ai_subtitle_urls:
                        self.ai_subtitle_urls.append(url)
                        self.log(f"Found ai_subtitle URL: {url}")
        except Exception as e:
            self.log(f"Failed to capture ai_subtitle request: {str(e)}")

    def save_urls(self):
        """Save collected ai_subtitle URLs to file"""
        try:
            with open("bilibili/ai_subtitle_urls.txt", "w", encoding="utf-8") as f:
                for url in self.ai_subtitle_urls:
                    f.write(url + '\n')
            self.log(f"Saved {len(self.ai_subtitle_urls)} URLs to bilibili/ai_subtitle_urls.txt")
        except Exception as e:
            self.log(f"Failed to save URLs: {str(e)}")

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