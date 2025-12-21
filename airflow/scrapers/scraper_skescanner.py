from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

origin = "LED"
destination = "sel"
ddate = "2026-06-03"
# rdate=2025-12-06 &dairport=led
URL = "https://ru.skyscanner.com/transport/flights/han/cxr/251212/?adultsv2=1&cabinclass=economy&childrenv2=&ref=home&rtn=0&outboundaltsenabled=false&inboundaltsenabled=false&preferdirects=false"

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.get(URL)
driver.maximize_window()
wait = WebDriverWait(driver, 25)

# Wait for flight result list
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".m-result-list")))

# Scroll to load all flights
for _ in range(2):
    driver.execute_script("window.scrollBy(0, 600);")
    time.sleep(1.0)

# ---------------------------------------------------------
# FIND ALL FLIGHT ITEMS BASED ON YOUR EXACT HTML SNIPPET
# ---------------------------------------------------------

flight_items = driver.find_elements(
    By.XPATH, "//div[@class='FlightsResults_dayViewItems__OGJkZ']//div[contains(@class,'FlightsTicketWrapper_itineraryContainer__OWNhY')]"
)

print(f"Found flights: {len(flight_items)}\n")

flights = []

for item in flight_items:
    # Airline name (S7 Airlines)
    try:
        airline = item.find_element(
            By.XPATH,
            ".//div[contains(@class,'flight-info-airline__flights')]//div[@data-testid='flights-name']",
        ).text
    except:
        airline = None

    # Departure time (11:55)
    try:
        depart_time = item.find_element(
            By.XPATH,
            ".//div[contains(@class,'is-departure')]//span[contains(@class,'time_cbcc')]",
        ).text
    except:
        depart_time = None

    # Departure airport (LED T1)
    try:
        depart_airport = item.find_element(
            By.XPATH,
            ".//div[contains(@class,'is-departure')]//span[contains(@class,'flight-info-stop__code')]",
        ).text
    except:
        depart_airport = None

    # Arrival time (13:30)
    try:
        arrive_time = item.find_element(
            By.XPATH,
            ".//div[contains(@class,'is-arrival')]//span[contains(@class,'time_cbcc')]",
        ).text
    except:
        arrive_time = None

    # Arrival airport (DME T1)
    try:
        arrive_airport = item.find_element(
            By.XPATH,
            ".//div[contains(@class,'is-arrival')]//span[contains(@class,'flight-info-stop__code')]",
        ).text
    except:
        arrive_airport = None

    # Duration (1h 35m)
    try:
        duration = item.find_element(
            By.XPATH, ".//div[@data-testid='flightInfoDuration']"
        ).text
    except:
        duration = None

    # Nonstop / Stops
    try:
        stop_type = item.find_element(
            By.XPATH, ".//span[@data-testid='stopInfoText']"
        ).text
    except:
        stop_type = None

    # PRICE (not included in snippet but normally exists)
    try:
        price = item.find_element(
            By.XPATH,
            ".//span[contains(@class,'price') or contains(@class,'total-price')]",
        ).text
    except:
        price = None

    try:
        baggage_icons = item.find_elements(
            By.XPATH,
            ".//*[contains(@class,'icon_luggage') or contains(@class,'icon_baggage')]",
        )
        baggage_included = len(baggage_icons) > 0
    except:
        baggage_included = None

    try:
        seats_el = item.find_elements(
            By.XPATH,
            ".//*[contains(text(), 'left') or contains(text(), 'Only') or contains(text(),'ост')]",
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

driver.quit()

for f in flights:
    print(f)


# text_box = driver.find_element(by=By.NAME, value="my-text")
# submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")

# text_box.send_keys("Selenium")
# submit_button.click()

# message = driver.find_element(by=By.ID, value="message")
# text = message.text
#
