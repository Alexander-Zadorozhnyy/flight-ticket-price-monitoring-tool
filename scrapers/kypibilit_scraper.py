import re

from impit import TimeoutException
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import undetected_chromedriver as uc


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
ddate = "0406"

URL = f"https://www.kupibilet.ru/search?adult=1&cabinClass=Y&child=0&childrenAges=[]&infant=0&route[0]=iatax:LED_2025-12-18_date_2025-12-18_iatax:CAN&v=2"
print(f"{URL=}")

# Create driver in HEADLESS mode
with uc.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
) as driver:
    driver.get(URL)
    wait = WebDriverWait(driver, 25)

    # Wait for list
    try:
        wait.until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, '[data-testid="serp-ticket-item"]')
            )
        )
    except TimeoutException:
        print("Flight results not loaded — page may be blocking headless browser")
        driver.save_screenshot("tripcom_timeout.png")
        driver.quit()
        exit()

    # Parse flights
    tickets = driver.find_elements(By.CSS_SELECTOR, '[data-testid="serp-ticket-item"]')

    print(f"Found flights: {len(tickets)}\n")

    flights = []

    for ticket in tickets:
        try:
            flights.append(parse_ticket(ticket))
        except Exception as e:
            print("Error while parsing ticket:", e)

    for f in flights:
        print(f)
