from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time, os, requests, re
# Create a new Chrome WebDriver instance
driver = webdriver.Chrome()
driver.maximize_window()
 
# Navigate to a website
driver.get("https://www.fia.com/documents/championships/fia-formula-one-world-championship-14/season/season-2022-2005")
 
wait = WebDriverWait(driver, 20)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "decision-document-list")))

try:
    cookie_button = WebDriverWait(driver, 5).until(
        EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Accept All')]"))
    )
    driver.execute_script("arguments[0].click();", cookie_button)
    print("✅ Dismissed cookie banner")
    time.sleep(2)
except Exception as e:
    print("⚠️ No cookie banner appeared (or already gone)")


# === Step 2: Count how many ULs are in that container ===
div_element = driver.find_element(By.XPATH, "//*[@id='list-view']/div[3]/div/div[2]/div")
ul_elements = div_element.find_elements(By.TAG_NAME, "ul")
uls = len(ul_elements)
#uls = driver.find_elements(By.XPATH, "//*[@id="list-view"]/div[3]/div/div[2]/div")
print(f"Found {uls} GP panels")

for i in range(1, uls + 1):
    try:
        element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[4]/div/div/div[4]/div[2]/div/div[3]/div/div[2]/div/ul[{i}]")))
        element.click()
        time.sleep(8)
    except Exception as e:
        print(f"Error clicking element {i}: {e}")

#driver.find_element(By.XPATH, "/html/body/div[4]/div/div/div[4]/div[2]/div/div[3]/div/div[2]/div/ul[1]").click()
#driver.find_element(By.XPATH, "/html/body/div[4]/div/div/div[4]/div[2]/div/div[3]/div/div[2]/div/ul[2]").click()
#driver.find_element(By.XPATH, "/html/body/div[4]/div/div/div[4]/div[2]/div/div[3]/div/div[2]/div/ul[3]").click()
time.sleep(10)  # Wait for the page to load after clicking
 #Print the page source
page_source = driver.page_source
with open("page_source.html", "w", encoding="utf-8") as f:
    f.write(page_source)
print("✅ Saved full page source after all panels expanded.")
print(page_source)
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

        # === Dynamically extract year ===
        match = re.match(r"(\d{4})_(.+)", filename)
        if match:
            year = match.group(1)  # e.g. '2025'
            filename_clean = match.group(2)
        else:
            year = "2022"
            filename_clean = filename

        # === Extract GP folder name ===
        if "grand_prix" in filename_clean:
            gp_folder = filename_clean.split("-")[0].strip().lower().replace(" ", "_")
            if "grand_prix" not in gp_folder:
                gp_folder += "_grand_prix"
        else:
            gp_folder = "unknown_gp"

        # === Create full folder path: year/gp_folder ===
        full_folder = os.path.join(year, gp_folder)
        os.makedirs(full_folder, exist_ok=True)

        # === Build full download path ===
        full_url = "https://www.fia.com" + href
        file_path = os.path.join(full_folder, filename)

        try:
            r = requests.get(full_url)
            with open(file_path, "wb") as f:
                f.write(r.content)
            downloaded += 1
            print(f"⬇️ Downloaded: {file_path}")
        except Exception as e:
            print(f"❌ Failed: {full_url} — {e}")




print(f"\n✅ Finished: {downloaded} PDF documents downloaded into folders.")
