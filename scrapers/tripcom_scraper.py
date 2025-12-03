import time

from impit import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc

# -----------------------------
# HEADLESS CHROME OPTIONS
# -----------------------------
options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # Modern headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

origin = "LED"
destination = "SVO"
ddate = "2025-12-03"

URL = (
    f"https://www.trip.com/flights/showfarefirst?"
    f"dcity={origin}&acity={destination}&ddate={ddate}"
    "&triptype=ow&class=y&lowpricesource=searchform&quantity=1"
    "&searchboxarg=t&nonstoponly=off&locale=en-XX&curr=RUB"
)

# Create driver in HEADLESS mode
with uc.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
) as driver:
    driver.get(URL)
    wait = WebDriverWait(driver, 25)

    # Wait for list
    try:
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".m-result-list")))
    except TimeoutException:
        print("Flight results not loaded — page may be blocking headless browser")
        driver.save_screenshot("tripcom_timeout.png")
        driver.quit()
        exit()

    # Scroll to load flights
    for _ in range(2):
        driver.execute_script("window.scrollBy(0, 800);")
        time.sleep(1.0)

    # Parse flights
    flight_items = driver.find_elements(
        By.XPATH, "//div[@class='m-result-list']//div[contains(@class,'result-item')]"
    )

    print(f"Found flights: {len(flight_items)}\n")

    flights = []

    for item in flight_items:

        def safe(xpath):
            try:
                return item.find_element(By.XPATH, xpath).text
            except:
                return None

        airline = safe(
            ".//div[contains(@class,'flight-info-airline__flights')]//div[@data-testid='flights-name']"
        )
        depart_time = safe(
            ".//div[contains(@class,'is-departure')]//span[contains(@class,'time_cbcc')]"
        )
        depart_airport = safe(
            ".//div[contains(@class,'is-departure')]//span[contains(@class,'flight-info-stop__code')]"
        )
        arrive_time = safe(
            ".//div[contains(@class,'is-arrival')]//span[contains(@class,'time_cbcc')]"
        )
        arrive_airport = safe(
            ".//div[contains(@class,'is-arrival')]//span[contains(@class,'flight-info-stop__code')]"
        )
        duration = safe(".//div[@data-testid='flightInfoDuration']")
        stop_type = safe(".//span[@data-testid='stopInfoText']")
        price = safe(
            ".//span[contains(@class,'price') or contains(@class,'total-price')]"
        )

        # --- BAGGAGE (carry-on included) ---
        baggage_included = False
        try:
            baggage_elem = item.find_element(
                By.XPATH, ".//*[@data-testid='list_label_hand_baggages']"
            )
            if baggage_elem:
                text = baggage_elem.text.lower()
                if "included" in text:
                    baggage_included = True
        except:
            baggage_included = False

        # --- BAGGAGE (carry-on included) ---
        try:
            seats_el = item.find_elements(
                By.XPATH,
                ".//*[contains(text(),'left') or contains(text(),'Only') or contains(text(),'ост')]",
            )
            seats_left = seats_el[0].text if seats_el else None
        except:
            seats_left = None

        flights.append(
            {
                "airline": airline,
                "departure_time": depart_time,
                "departure_airport": depart_airport,
                "arrival_time": arrive_time,
                "arrival_airport": arrive_airport,
                "duration": duration,
                "stop_type": stop_type,
                "price": price,
                "baggage_included": baggage_included,
                "seats_left": seats_left,
            }
        )

    for f in flights:
        print(f)
