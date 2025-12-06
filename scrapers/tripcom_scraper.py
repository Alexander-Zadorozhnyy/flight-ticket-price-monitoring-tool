from datetime import datetime
import re
import time
from typing import Optional

from impit import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def construct_url(
    origin: str,
    destination: str,
    departure_date: datetime,
    return_date: Optional[datetime],
    adults: int,
):
    url = f"https://www.trip.com/flights/showfarefirst?quantity={adults}&dcity={origin}&acity={destination}&ddate={departure_date.year}-{departure_date.month}-{departure_date.day}&triptype=rt&class=y&lowpricesource=searchform&searchboxarg=t&nonstoponly=off&locale=en-XX&curr=RUB"

    if return_date:
        url += f"&rdate={return_date.year}-{return_date.month}-{return_date.day}"

    return url


def parse_ticket(ticket):
    def safe(xpath):
        try:
            return ticket.find_element(By.XPATH, xpath).text
        except:
            return None

    airline = safe(
        ".//div[contains(@class,'flight-info-airline__flights')]//div[@data-testid='flights-name']"
    )
    departure_time = safe(
        ".//div[contains(@class,'is-departure')]//span[contains(@class,'time_cbcc')]"
    )
    departure_airport = safe(
        ".//div[contains(@class,'is-departure')]//span[contains(@class,'flight-info-stop__code')]"
    )
    arrival_time = safe(
        ".//div[contains(@class,'is-arrival')]//span[contains(@class,'time_cbcc')]"
    )
    arrival_airport = safe(
        ".//div[contains(@class,'is-arrival')]//span[contains(@class,'flight-info-stop__code')]"
    )
    duration = safe(".//div[@data-testid='flightInfoDuration']")
    stop_type = safe(".//span[@data-testid='stopInfoText']")
    price = safe(".//span[contains(@class,'price') or contains(@class,'total-price')]")

    # --- BAGGAGE (carry-on included) ---
    baggage_included = False
    try:
        baggage_elem = ticket.find_element(
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
        seats_el = ticket.find_elements(
            By.XPATH,
            ".//*[contains(text(),'left') or contains(text(),'Only') or contains(text(),'ост')]",
        )
        seats_left = seats_el[0].text if seats_el else None
    except:
        seats_left = None

    return {
        "airline": airline,
        "departure_time": departure_time,
        "departure_airport": departure_airport,
        "arrival_time": arrival_time,
        "arrival_airport": arrival_airport,
        "duration": duration,
        "stop_type": stop_type,
        "price": price,
        "baggage_included": baggage_included,
        "seats_left": seats_left,
    }


def scrape_flights(
    origin: str,
    destination: str,
    departure_date: datetime,
    return_date: Optional[datetime],
    adults: int = 1,
    options: Optional[webdriver.ChromeOptions] = None,
) -> list:
    """
    Scrape flights from KupiBilet.ru website.

    Args:
        origin: IATA code of departure airport (e.g., 'LED')
        destination: IATA code of arrival airport (e.g., 'SVO')
        departure_date: Departure date in format 'MMDD' (e.g., '0406' for April 6th)
        options: Chrome options for Selenium (optional)

    Returns:
        List of flight dictionaries or parsed objects
    """
    # Parse date components
    url = construct_url(origin, destination, departure_date, return_date, adults)
    print(f"Scraping URL: {url}")

    flights = []

    if options is None:
        options = webdriver.ChromeOptions()
        options.add_argument("--headless=new")  # Modern headless mode
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")

    # Create driver in HEADLESS mode
    with uc.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    ) as driver:
        driver.get(url)
        wait = WebDriverWait(driver, 25)

        # Wait for list
        try:
            wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, ".m-result-list"))
            )
        except TimeoutException:
            print("Flight results not loaded — page may be blocking headless browser")
            # driver.save_screenshot("tripcom_timeout.png")
            driver.quit()
            exit()

        for _ in range(2):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.0)

        # Parse flights
        tickets = driver.find_elements(
            By.XPATH,
            "//div[@class='m-result-list']//div[contains(@class,'result-item')]",
        )

        print(f"Found flights: {len(tickets)}\n")

        for ticket in tickets:
            try:
                flights.append(parse_ticket(ticket))
            except Exception as e:
                print("Error while parsing ticket:", e)

    return flights


# -----------------------------
# HEADLESS CHROME OPTIONS
# -----------------------------
origin = "LED"
destination = "SVO"
ddate = datetime(2025, 12, 11)
rdate = datetime(2025, 12, 14)

options = webdriver.ChromeOptions()
options.add_argument("--headless=new")  # Modern headless mode
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

flights = scrape_flights(
    origin=origin,
    destination=destination,
    departure_date=ddate,
    options=options,
    return_date=rdate,
)
print(f"{flights=}")
