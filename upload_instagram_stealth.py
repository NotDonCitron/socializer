import re
import sys
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
from urllib.parse import unquote

def get_hashtags(driver, seed_word):
    print(f"Generating hashtags for topic: {seed_word}...")
    try:
        # 1.5 Handle Popups (Turn on Notifications)
        try:
            popup_btn = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Not Now')] | //button[contains(text(), 'Jetzt nicht')]"))
            )
            popup_btn.click()
            time.sleep(1)
        except:
            pass

        # 2. Search Logic
        
        # Click Search Icon (Magnifying Glass)
        search_selectors = [
             "//svg[@aria-label='Search']", 
             "//svg[@aria-label='Suchen']",
             "//svg[contains(@aria-label, 'Suchen')]",
             "//span[text()='Search']", 
             "//span[text()='Suchen']",
             "//a[@href='#']//span[contains(text(), 'Search')]",
             "//a[@href='#']//span[contains(text(), 'Suchen')]"
        ]
        
        search_btn = None
        for sel in search_selectors:
            try:
                found = driver.find_elements(By.XPATH, sel)
                for el in found:
                     if el.is_displayed():
                         search_btn = el
                         if search_btn.tag_name == 'svg':
                             search_btn = search_btn.find_element(By.XPATH, "./../..")
                         break
                if search_btn:
                    break
            except:
                continue
                
        typed_search = False
        if not search_btn:
            print("Could not find Search button. Trying fallback URL...")
            driver.get(f"https://www.instagram.com/explore/tags/{seed_word}/")
            time.sleep(5)
        else:
            search_btn.click()
            time.sleep(2)
            
            # Type into the search input
            try:
                search_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//input[@placeholder='Search'] | //input[@placeholder='Suchen']"))
                )
                search_input.send_keys(f"#{seed_word}")
                typed_search = True
            except:
                print("Could not find search input.")
            
        time.sleep(4) 
        
        # Scrape results
        found_tags = []
        if typed_search:
            results = driver.find_elements(By.XPATH, "//a[contains(@href, '/explore/tags/')]")
            for res in results:
                text = res.text.split("\n")[0]
                if text.startswith("#"):
                    found_tags.append(text)
        
        # Fallback
        if not found_tags:
            print("No tags found in dropdown. Scraping from top post...")
            try:
                first_post = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/p/')]"))
                )
                first_post.click()
                time.sleep(3)
                caption_el = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, "//h1/.. | //li[@role='menuitem']//span"))
                )
                found_tags = re.findall(r"#\w+", caption_el.text)
                
                # Close modal to return to clean state
                try:
                    close_btn = driver.find_element(By.XPATH, "//svg[@aria-label='Close'] | //button[contains(text(), 'Close')]")
                    close_btn.click()
                except:
                    driver.back() # Fallback navigation
                
            except Exception as e:
                print(f"Could not scrape post: {e}")

        # Limit to 15 tags
        return found_tags[:15]
        
    except Exception as e:
        print(f"Hashtag generation error: {e}")
        return []

def main():
    print("=== Instagram Stealth Uploader ===")
    
    # Get file path from command line argument
    if len(sys.argv) > 1:
        global path_input
        path_input = sys.argv[1]
        print(f"Using file: {path_input}")
    else:
        print("No file path provided. Please provide a file path as argument.")
        return
    
    print("Initializing Chrome (this may take a few seconds)...")
    
    options = uc.ChromeOptions()
    # options.add_argument("--headless=new") # Keep headful for now to verify
    
    driver = uc.Chrome(options=options)
    driver.maximize_window()
    
    try:
        # 1. Go to domain to set cookies
        print("Navigating to Instagram...")
        driver.get("https://www.instagram.com/")
        time.sleep(3)
        
        # 2. Inject Cookies
        print("Injecting cookies...")
        manual_cookies = {
            "csrftoken": "F6aBaYkIGs0xPB5qkaAwdN",
            "datr": "qXRbadgtyvS6GGM_N00U7Wmi",
            "dpr": "2",
            "ds_user_id": "78167308557",
            "ig_did": "7F6BE45A-A1BD-4F63-BAF0-6F48F75FDC41",
            "mid": "aVt0qQAEAAE2pEO2OEHqv51J4qBK",
            "rur": "\"LDC\\05478167308557\\0541799137993:01fe9741d51b0b47d9e3738c365ace4b281dfa1294a4805ceddcc728b8f3bdf28cd86530\"",
            "sessionid": "78167308557%3AT0nfhYqfPFf11X%3A7%3AAYiCfHDQ1TP92tjmX6Yc5jX7TRxP8SM37gPzZDN2dQ"
            # Removed 'wd' cookie to prevent mobile layout
        }
        
        for name, value in manual_cookies.items():
            if "%" in value:
                value = unquote(value)
            
            driver.add_cookie({
                "name": name,
                "value": value,
                "domain": ".instagram.com",
                "path": "/"
            })
            
        # 3. Refresh to apply cookies
        print("Cookies set. Refreshing page...")
        driver.refresh()
        time.sleep(5)
        
        print("Checking login status...")
        if "login" in driver.current_url:
            print("ERROR: Still on login page. Cookies might be invalid or browser flagged.")
            input("Press Enter to close browser...")
            return

        print("Login seems successful!")
        
        # 5. File Upload Flow
        # Fix path string just in case
        if not os.path.exists(path_input):
            # Smart check: Did user mess up the extension?
            root, ext = os.path.splitext(path_input)
            possible_exts = [".png", ".jpg", ".jpeg", ".mp4", ".mov"]
            found_alt = None
            
            for alt in possible_exts:
                if os.path.exists(root + alt):
                    found_alt = root + alt
                    break
            
            if found_alt:
                print(f"⚠️ Original path not found, but I found this one: {found_alt}")
                print(f"Using {found_alt} instead.")
                path_input = found_alt
            else:
                print(f"❌ File not found at: {path_input}")
                return
            
        # Auto-generate caption and hashtags
        caption = ""
        topic = "screenshot"  # Default topic for screenshots
        print(f"Auto-generating caption for topic: {topic}")
        tags = get_hashtags(driver, topic)
        if tags:
            caption = f"Here is a nice photo about {topic}! 📸\n\n" + " ".join(tags)
            print(f"Generated Caption:\n{caption}")
        else:
            caption = f"Enjoying {topic}!"
            
        # Ensure we are back at home for upload
        if "instagram.com" not in driver.current_url or "explore" in driver.current_url:
            driver.get("https://www.instagram.com/")
            time.sleep(3)
        
        print(f"Uploading {path_input}...")
        
        # Try to find 'Create' button
        print("Looking for 'Create' button...")
        
        selectors = [
             "//svg[@aria-label='New post']",
             "//svg[@aria-label='Neuer Beitrag']", # German
             "//span[text()='Create']",
             "//span[text()='Erstellen']", # German
             "//div[text()='Create']",
             "//div[text()='Erstellen']", # German
             "//a[@href='#']//span[contains(text(), 'Create')]",
             "//a[@href='#']//span[contains(text(), 'Erstellen')]" # German
        ]
        
        create_btn = None
        for sel in selectors:
            try:
                found = driver.find_elements(By.XPATH, sel)
                if found:
                    create_btn = found[0]
                    # If SVG, get parent
                    if create_btn.tag_name == 'svg':
                         create_btn = create_btn.find_element(By.XPATH, "./../..")
                    print(f"Found Create button using: {sel}")
                    break
            except:
                continue
        
        if not create_btn:
            print("Could not find 'Create' button automatically.")
            print("Please CLICK THE [+] / 'Create' button in the browser manually NOW.")
            print("I will wait 10 seconds...")
            time.sleep(10)
        else:
            try:
                create_btn.click()
                print("Clicked Create button...")
            except Exception as e:
                print(f"Failed to click Create button: {e}")
                print("Please click it manually.")
                time.sleep(5)
        
        time.sleep(3)
        
        # Find file input
        try:
            # It usually appears in the DOM after "Create" is clicked
            file_input = driver.find_element(By.XPATH, "//input[@type='file']")
            file_input.send_keys(path_input)
            print("File sent to input...")
        except Exception as e:
            print(f"Could not find file input: {e}")
            print("Please drag and drop your file manually into the browser window.")
            time.sleep(10)
        
        # Flow for Next -> Next -> Share
        try:
            print("Waiting for 'Next' / 'Weiter' button...")
            time.sleep(3)
            
            # Helper to find button by multiple texts
            def find_clickable_by_texts(driver, texts):
                xpath = " | ".join([f"//div[text()='{t}']" for t in texts]) + " | " + " | ".join([f"//button[text()='{t}']" for t in texts])
                return WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable((By.XPATH, xpath))
                )

            next_btn = find_clickable_by_texts(driver, ["Next", "Weiter"])
            next_btn.click()
            print("Clicked Next (Crop)...")
            
            time.sleep(2)
            next_btn = find_clickable_by_texts(driver, ["Next", "Weiter"])
            next_btn.click()
            print("Clicked Next (Filter)...")
            
            time.sleep(2)
            try:
                caption_area = driver.find_element(By.XPATH, "//div[@aria-label='Write a caption...'] | //div[@aria-label='Verfasse eine Bildunterschrift ...']")
                caption_area.click()
                caption_area.send_keys(caption)
                print("Caption entered.")
            except:
                print("Could not find caption area automatically. Please type it manually.")
            
            print("Waiting for 'Share' / 'Teilen' button...")
            share_btn = find_clickable_by_texts(driver, ["Share", "Teilen"])
            share_btn.click()
            print("Clicked Share!")
            
            time.sleep(5)
            print("Done! Check the browser.")
            
        except Exception as e:
            print(f"Navigation error during post flow: {e}")
            print("You can finish the steps manually.")

    except Exception as e:
        print(f"Critical Automation Error: {e}")
    finally:
        print("Browser will remain open for 60 seconds so you can see what happened.")
        time.sleep(60)
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    main()
