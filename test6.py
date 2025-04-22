from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

class BilibiliSubtitleCrawler:
    def __init__(self):
        self.driver = None
        self.logs = []
        self.videos_with_subtitles = []

    def log(self, message):
        """Print log message to console"""
        print(message)

    def crawl(self):
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

            # 3. Load videos from JSON file
            try:
                with open("bilibili/videos1.json", "r", encoding="utf-8") as f:
                    videos = json.load(f)
                self.log(f"Loaded {len(videos)} videos from videos.json")
            except Exception as e:
                self.log(f"Failed to load videos.json: {str(e)}")
                return

            # 4. Process each video
            for video in videos:
                try:
                    alt = video.get("alt", "")
                    url = video.get("url", "")
                    
                    if not url:
                        self.log(f"Skipping video with empty URL: {alt}")
                        continue
                        
                    self.log(f"Processing video: {alt}")
                    self.log(f"Video URL: {url}")

                    # Open video in new tab
                    self.driver.execute_script("window.open('');")
                    self.driver.switch_to.window(self.driver.window_handles[-1])
                    self.driver.get(url)
                    self.log("Opened video page")

                    # Open subtitles
                    self.open_subtitle()
                    
                    # Wait for 2 seconds
                    time.sleep(2)

                    # Search for ai_subtitle
                    ai_subtitle_urls = self.search_ai_subtitle()
                    
                    # Save video info with subtitle URLs
                    video_data = {
                        "alt": alt,
                        "url": url,
                        "ai_subtitle_urls": ai_subtitle_urls
                    }
                    self.videos_with_subtitles.append(video_data)
                    self.log(f"Found {len(ai_subtitle_urls)} AI subtitle URLs for this video")

                    # Close the current tab and switch back to main tab
                    self.driver.close()
                    self.driver.switch_to.window(self.driver.window_handles[0])
                    self.log("Closed video tab")

                except Exception as e:
                    self.log(f"Error processing video {alt}: {str(e)}")
                    # Close tab if open and switch back
                    if len(self.driver.window_handles) > 1:
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])

            # Save results to JSON file
            self.save_results()

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
        """Search for ai_subtitle network requests and return found URLs"""
        ai_subtitle_urls = []
        
        if not self.driver:
            self.log("Browser not running")
            return ai_subtitle_urls

        try:
            # Get performance logs
            logs = self.driver.get_log("performance")
            self.logs.extend(logs)
            for entry in logs:
                try:
                    log = json.loads(entry["message"])["message"]
                    if "params" in log and "response" in log["params"] and "url" in log["params"]["response"]:
                        url = log["params"]["response"]["url"]
                        if "aisubtitle" in url.lower() and url not in ai_subtitle_urls:
                            ai_subtitle_urls.append(url)
                            self.log(f"Found ai_subtitle URL: {url}")
                except:
                    continue
        except Exception as e:
            self.log(f"Failed to capture ai_subtitle request: {str(e)}")
            
        return ai_subtitle_urls

    def save_results(self):
        """Save collected video data with subtitles to JSON file"""
        try:
            with open("bilibili/videos_with_ai_subtitle.json", "w", encoding="utf-8") as f:
                json.dump(self.videos_with_subtitles, f, ensure_ascii=False, indent=2)
            self.log(f"Saved results for {len(self.videos_with_subtitles)} videos to videos_with_ai_subtitle.json")
        except Exception as e:
            self.log(f"Failed to save results: {str(e)}")

    def quit_browser(self):
        """Close browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.log("Browser closed")

if __name__ == "__main__":
    crawler = BilibiliSubtitleCrawler()
    crawler.crawl()