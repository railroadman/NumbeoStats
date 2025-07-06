import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
from datetime import datetime
import xml.etree.ElementTree as ET
import os
import sys
from db_writer import init_db, insert_dataframe

# ✅ Страны Европы и не только
COUNTRIES = [
    "Ukraine", "Germany", "France", "Poland", "Switzerland",
    "Norway", "Czech Republic", "Romania", "Italy", "Spain", "United Kingdom"
]

# ✅ Валюты по странам
country_currency_map = {
    "Ukraine": "UAH",
    "Germany": "EUR",
    "France": "EUR",
    "Poland": "PLN",
    "Switzerland": "CHF",
    "Norway": "NOK",
    "Czech Republic": "CZK",
    "Romania": "RON",
    "Italy": "EUR",
    "Spain": "EUR",
    "United Kingdom": "GBP"
}

today = datetime.now().strftime("%Y-%m-%d")

if os.path.exists(f"european_food_prices_{today}.xlsx"):
    print(f"Data for this day {today} already grabbed ")
    sys.exit()

# ✅ Извлекаем числовую цену из текста (например "€2.49" → 2.49)
def extract_price(text):
    match = re.search(r"[\d,.]+", text)
    if match:
        number = match.group(0).replace(",", ".")
        try:
            return float(number)
        except ValueError:
            return None
    return None

# ✅ Получаем курсы валют к евро
def get_currency_rates_to_eur():
    url = "https://www.ecb.europa.eu/stats/eurofxref/eurofxref-daily.xml"
    response = requests.get(url)
    response.raise_for_status()
    tree = ET.fromstring(response.content)

    ns = {'gesmes': 'http://www.gesmes.org/xml/2002-08-01',
          'default': 'http://www.ecb.int/vocabulary/2002-08-01/eurofxref'}

    currency_to_eur = {"EUR": 1.0}
    for cube in tree.findall(".//default:Cube[@currency]", namespaces=ns):
        currency = cube.attrib["currency"]
        rate = float(cube.attrib["rate"])
        currency_to_eur[currency] = 1 / rate
    
    country_currency_map = {
        "Ukraine": "UAH",
        "Germany": "EUR",
        "France": "EUR",
        "Poland": "PLN",
        "Switzerland": "CHF",
        "Norway": "NOK",
        "Czech Republic": "CZK",
        "Romania": "RON",
        "Italy": "EUR",
        "Spain": "EUR",
        "United Kingdom": "GBP"
    }

    result = {}
    for country, code in country_currency_map.items():
        result[country] = currency_to_eur.get(code, None)
    return result

BASE_URL = "https://www.numbeo.com/cost-of-living/country_result.jsp?country="


def fetch_prices_from_html(country):
    url = BASE_URL + country.replace(" ", "+")
    print(f"⏳ Загружаю: {url}")
    response = requests.get(url)
    if response.status_code != 200:
        print(f"❌ Ошибка загрузки страницы {country}")
        return []

    soup = BeautifulSoup(response.content, "html.parser")
    table = soup.find("table", class_="data_wide_table")
    if not table:
        print(f"⚠️ Table not found on page {country}")
        return []

    data = []
    rows = table.find_all("tr")[1:]
    for row in rows:
        cols = row.find_all("td")
        if len(cols) >= 2:
            item = cols[0].get_text(strip=True)
            price_text = cols[1].get_text(strip=True)
            price_value = extract_price(price_text)

            if price_value is not None:
                data.append({
                    "Country": country,
                    "Product": item,
                    "Price (Local Currency)": price_value
                })
    print(f"✅ Found {len(data)} products in {country}")
    return data

def safe_convert_to_eur(row):
    try:
        price = row["Price (Local Currency)"]
        country = row["Country"]
        rate = currency_rates.get(country)
        if (rate is None and country=='Ukraine'):
            return round(price * uah_rate,2)

        if pd.notnull(price) and rate is not None:
            return round(price * rate, 2)
        else:
            
            print(f"⚠️ Skipped: {country}, price={price}, rate={rate}")
            return None
    except Exception as e:
        print(f"❌ Error in a price calculation: {row} → {e}")
        return None
def get_uah_to_eur_from_nbu():
    url = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange?valcode=EUR&json"
    response = requests.get(url)
    response.raise_for_status()
    rate = response.json()[0]["rate"]
    return 1 / rate  # 1 UAH = X EUR

uah_rate = get_uah_to_eur_from_nbu()
# ✅ Основной сбор
all_data = []
for country in COUNTRIES:
    try:
        all_data.extend(fetch_prices_from_html(country))
        time.sleep(10)  # чтобы не перегрузить Numbeo
    except Exception as e:
        print(f"❌ Ошибка при обработке {country}: {e}")

df = pd.DataFrame(all_data)

if df.empty:
    print("⚠️ Can get data data is empty.")
    exit()

# ✅ Добавим цену в евро
currency_rates = get_currency_rates_to_eur()
df["Price (EUR)"] = df.apply(safe_convert_to_eur, axis=1)

# ✅ Добавим дату

df["Date"] = today

# ✅ Сохраняем в Excel
filename = f"european_food_prices_{today}.xlsx"
print(f"📄 Data save to file: {filename}")
df.to_excel(filename, index=False)
# save to sqlite db
init_db()
insert_dataframe(df)
print(f"📄 Data save to  DB")


