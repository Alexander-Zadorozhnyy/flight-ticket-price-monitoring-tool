from datetime import datetime
import re
from typing import Optional

from impit import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


def adjust_date(num):
    if num < 10:
        return f"0{num}"

    return num


def construct_url(
    origin: str,
    destination: str,
    departure_date: datetime,
    return_date: Optional[datetime],
    adults: int,
):
    url = f"https://www.kupibilet.ru/search?adult={adults}&cabinClass=Y&child=0&infant=0&route[0]=iatax:{origin}_{departure_date.year}-{adjust_date(departure_date.month)}-{adjust_date(departure_date.day)}_date_{departure_date.year}-{adjust_date(departure_date.month)}-{adjust_date(departure_date.day)}_iatax:{destination}"

    if return_date:
        url += f"&route[1]=iatax:{destination}_{return_date.year}-{adjust_date(return_date.month)}-{adjust_date(return_date.day)}_date_{return_date.year}-{adjust_date(return_date.month)}-{adjust_date(return_date.day)}_iatax:{origin}"

    return url


def parse_ticket(ticket):
    get = lambda selector: ticket.find_element(By.CSS_SELECTOR, selector)
    gettext = lambda selector: get(selector).text.strip()

    # --- Airline (icons → airline codes in img src)
    airline_imgs = ticket.find_elements(
        By.CSS_SELECTOR, '[data-testid="airline-icon"] img'
    )
    airline = ",".join(
        [img.get_attribute("src").split("/")[-1].split(".")[0] for img in airline_imgs]
    )

    # --- Times
    departure_time = gettext('[data-testid="serp-ticket-departure-time"]')
    arrival_time = gettext('[data-testid="serp-ticket-arrival-time"]')

    # --- Airports
    departure_airport_raw = gettext('[data-testid="serp-ticket-departure-info"]')
    arrival_airport_raw = gettext('[data-testid="serp-ticket-arrival-info"]')

    # Normalize: "Пулково (LED)" → "LED"

    extract_code = lambda t: (m.group(1) if (m := re.search(r"\((.*?)\)", t)) else t)

    departure_airport = extract_code(departure_airport_raw)
    arrival_airport = extract_code(arrival_airport_raw)

    # --- Duration
    duration = gettext('[data-testid="search-trip-duration"]')

    # --- Stops (e.g., "1 пересадка, 1ч 50м")
    try:
        stop_type = gettext('[data-testid="serp-ticket-transfer-text"]')
    except:
        stop_type = "Без пересадок"

    # --- Price (h1 element)
    price = gettext('[data-testid="serp-ticket-total-sum"] h1')

    # --- Baggage
    try:
        baggage_text = gettext('[data-testid="baggage-wrapper"]')
        baggage_included = True if "Багаж" in baggage_text else False
    except:
        baggage_included = False

    # --- Seats left ("Осталось X мест") – not always present
    try:
        seats_left_el = ticket.find_element(By.XPATH, ".//*[contains(text(),'мест')]")
        seats_left = seats_left_el.text.strip()
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
    return_date: Optional[datetime] = None,
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

    # Create driver in HEADLESS mode
    try:
        with uc.Chrome(
            driver_executable_path="/home/airflow/chromedriver",  # ✅ system driver
            browser_executable_path="/usr/bin/chromium",  # ✅ system chromium
            options=options,
            # service=Service(ChromeDriverManager().install()), options=options
        ) as driver:
            driver.get(url)
            wait = WebDriverWait(driver, 25)

            # Wait for list
            try:
                wait.until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-testid="serp-ticket-item"]')
                    )
                )
            except TimeoutException:
                print(
                    "Flight results not loaded — page may be blocking headless browser"
                )
                # driver.save_screenshot("tripcom_timeout.png")
                driver.quit()
                exit()

            # Parse flights
            tickets = driver.find_elements(
                By.CSS_SELECTOR, '[data-testid="serp-ticket-item"]'
            )

            print(f"Found flights: {len(tickets)}\n")

            for ticket in tickets:
                try:
                    flights.append(parse_ticket(ticket))
                except Exception as e:
                    print("Error while parsing ticket:", e)
    except TimeoutException:
        print("Get Timeout Exception")
    return flights


if __name__ == "__main__":
    origin = "LED"
    destination = "SVO"
    ddate = datetime(2025, 12, 30)
    rdate = datetime(2025, 12, 31)

    flights = scrape_flights(
        origin=origin,
        destination=destination,
        departure_date=ddate,
        return_date=rdate,
    )
    print(f"{flights=}")
