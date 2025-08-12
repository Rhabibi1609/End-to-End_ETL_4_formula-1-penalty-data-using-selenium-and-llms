from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time, os, requests

# === Step 1: Launch and navigate ===
driver = webdriver.Chrome()
driver.maximize_window()
driver.get("https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2024-2043")

wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "decision-document-list")))

# === Step 2: Count how many ULs are in that container ===
div_element = driver.find_element(By.XPATH, "//*[@id='list-view']/div[3]/div/div[2]/div")
ul_elements = div_element.find_elements(By.TAG_NAME, "ul")
uls = len(ul_elements)
#uls = driver.find_elements(By.XPATH, "//*[@id="list-view"]/div[3]/div/div[2]/div")
print(f"Found {uls} GP panels")

# === Step 3: Click each GP panel using absolute XPath ===
for i in range(1, uls + 1):
    try:
        xpath = f"/html/body/div[4]/div/div/div[4]/div[2]/div/div[3]/div/div[2]/div/ul[{i}]"
        panel = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView(true);", panel)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", panel)
        time.sleep(10)
        
        print(f"Clicked panel {i}")
        time.sleep(10)  # wait for documents to load
    except Exception as e:
        print(f"Failed to click panel {i}: {e}")

# === Step 4: Save the final expanded page source ===
time.sleep(15)
page_source = driver.page_source
with open("page_source.html", "w", encoding="utf-8") as f:
    f.write(page_source)
print("✅ Saved full page source after all panels expanded.")
driver.quit()

#print(page_source)
# === Step 5: Parse with BeautifulSoup and download PDFs ===
with open("page_source.html", "r", encoding="utf-8") as f:
    soup = BeautifulSoup(f, "html.parser")

pdf_links = soup.find_all("a", href=True)

downloaded = 0
for link in pdf_links:
    href = link["href"]
    if "/decision-document/" in href and href.endswith(".pdf"):
        filename = href.split("/")[-1]
        parts = filename.split("_")

        if len(parts) > 2:
            gp_parts = parts[1:-3]  # crude logic to extract "canadian_grand_prix"
            gp_folder = "_".join(gp_parts).lower()
        else:
            gp_folder = "unknown_gp"

        os.makedirs(gp_folder, exist_ok=True)
        full_url = "https://www.fia.com" + href
        file_path = os.path.join(gp_folder, filename)

        try:
            r = requests.get(full_url)
            with open(file_path, "wb") as f:
                f.write(r.content)
            downloaded += 1
            print(f"⬇️ Downloaded: {file_path}")
        except Exception as e:
            print(f"❌ Failed: {full_url} — {e}")

print(f"\n✅ Finished: {downloaded} PDF documents downloaded into folders.")
