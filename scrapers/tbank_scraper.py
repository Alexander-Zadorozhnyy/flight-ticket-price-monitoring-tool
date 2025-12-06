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
URL = f"https://www.tbank.ru/travel/flights/multi-way/LED-MOW/12-11/MOW-LED/12-14/?adults=2&children=0&infants=0&cabin=Y&composite=0"

for x in range(10):
    # ---------------------------------------------------------
    # FIND ALL FLIGHT ITEMS BASED ON YOUR EXACT HTML SNIPPET
    # ---------------------------------------------------------
    time.sleep(5)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    driver.get(URL)
    driver.maximize_window()
    wait = WebDriverWait(driver, 25)

    # Wait for flight result list
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.VirtualList__itemsContainer_QK31k")
        )
    )

    # Scroll to load all flights
    for _ in range(5):
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(1.0)
        
    flight_items = driver.find_elements(
        By.XPATH,
        "//div[@class='VirtualList__itemsContainer_QK31k']//div[contains(@class,'VirtualList__item_qgnAF')]",
    )

    print(f"Found flights: {len(flight_items)}\n") # TODO: getting only first 9 values and also add airlines cash back field

    flights = []

    for item in flight_items:

        def safe_find_text(by, selector):
            """Helper to safely extract text from element."""
            try:
                element = item.find_element(by, selector)
                return element.text.strip() if element.text else None
            except:
                return None

        def safe_find_elements(by, selector):
            """Helper to safely find multiple elements."""
            try:
                return item.find_elements(by, selector)
            except:
                return []

        # Airline
        airline = safe_find_text(By.CSS_SELECTOR, ".AirCompanies__title_UIWyE")

        # Departure time (20:45)
        depart_time = safe_find_text(
            By.CSS_SELECTOR, ".TimePlace__timePlace_left_XXmuF .TimePlace__time_L6k1z"
        )

        # Departure airport (LED)
        depart_airport = safe_find_text(
            By.CSS_SELECTOR, ".TimePlace__timePlace_left_XXmuF .TimePlace__code_bZVgy"
        )

        # Arrival time (22:15)
        arrive_time = safe_find_text(
            By.CSS_SELECTOR, ".TimePlace__timePlace_right_EFK4K .TimePlace__time_L6k1z"
        )

        # Arrival airport (SVO)
        arrive_airport = safe_find_text(
            By.CSS_SELECTOR, ".TimePlace__timePlace_right_EFK4K .TimePlace__code_bZVgy"
        )

        # Duration (В пути 1ч 30м)
        duration_raw = safe_find_text(By.CSS_SELECTOR, ".TotalTime__time_bs7xV")
        # Clean up duration text
        duration = None
        if duration_raw:
            # Extract just the time part (1ч 30м)
            import re

            match = re.search(r"(\d+ч(?:\s*\d+м)?)", duration_raw)
            if match:
                duration = match.group(1)
            else:
                duration = duration_raw

        # Stop type (Прямой = Direct)
        stop_type = safe_find_text(
            By.CSS_SELECTOR, ".TransfersList__transfersItem_TT5qL"
        )
        # Translate Russian to English if needed
        if stop_type == "Прямой":
            stop_type = "Nonstop"

        # Price (12 031 ₽)
        price_raw = safe_find_text(By.CSS_SELECTOR, ".Money-module__money_UZBbh")
        price = None
        if price_raw:
            # Clean price text
            price = price_raw.replace("\xa0", " ").strip()

        # Baggage information
        baggage_text = safe_find_text(
            By.CSS_SELECTOR, ".BaggageOffers__baggageDescription_uKNDn"
        )
        baggage_included = None
        if baggage_text:
            baggage_included = (
                "Без багажа" not in baggage_text
                and "без багажа" not in baggage_text.lower()
            )

        # Alternative baggage check using icons
        if baggage_included is None:
            baggage_icons = safe_find_elements(
                By.CSS_SELECTOR,
                ".BaggageOffers__baggage_TcSQn[data-qa-available='true']",
            )
            baggage_included = len(baggage_icons) > 0

        # Seats left - harder to find in this HTML, might be in other elements
        # Checking for any text indicating seats
        seats_texts = []

        # Check in various possible locations
        possible_seat_selectors = [
            ".PriceLayout__container_eq30B",
            ".FlightPanelActionsLayout__primaryAction_YYvNv",
            ".FlightCardLayout__topLeftLabels_NrHHV",
        ]

        for selector in possible_seat_selectors:
            elements = safe_find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.text.strip()
                if text and any(
                    keyword in text.lower()
                    for keyword in ["left", "осталось", "мест", "осталось", "only"]
                ):
                    seats_texts.append(text)

        seats_left = seats_texts[0] if seats_texts else None

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

driver.quit()
# text_box = driver.find_element(by=By.NAME, value="my-text")
# submit_button = driver.find_element(by=By.CSS_SELECTOR, value="button")

# text_box.send_keys("Selenium")
# submit_button.click()

# message = driver.find_element(by=By.ID, value="message")
# text = message.text
#
