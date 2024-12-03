import requests 
from bs4 import BeautifulSoup 
from selenium import webdriver 
from selenium.webdriver.chrome.options import Options 
import pandas as pd 
from datetime import datetime
import time
import re
from urllib.parse import urljoin
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class WebScraper:     
    def __init__(self, config):         
        self.config = config         
        self.setup_selenium()      
        
    def setup_selenium(self):         
        chrome_options = Options()         
        chrome_options.add_argument('--headless')         
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        chrome_options.add_argument(f'user-agent={user_agent}')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": user_agent})
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

    def scrape_amazon_page(self, url):
        data = []
        try:
            self.driver.get(url)
            time.sleep(7)
            
            # Scroll to load dynamic content
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all possible product titles using multiple selectors
            product_titles = []
            title_selectors = [
                'span.a-size-medium.a-color-base.a-text-normal',  # Main product titles
                'span.a-size-base-plus.a-color-base.a-text-normal',  # Secondary product titles
                'a.a-link-normal span.a-size-base-plus'  # Linked product titles
            ]
            
            for selector in title_selectors:
                titles = soup.select(selector)
                product_titles.extend(titles)
                print(f"Found {len(titles)} titles with selector: {selector}")
                if titles:
                    print(f"Sample title: {titles[0].text.strip()[:100]}...")
            
            # Find all prices
            prices = []
            price_containers = soup.find_all('span', class_='a-price')
            
            for price_container in price_containers:
                # Try offscreen price first
                offscreen_price = price_container.find('span', class_='a-offscreen')
                if offscreen_price:
                    prices.append(offscreen_price)
                    continue
                    
                # Otherwise try to construct from whole and fraction
                whole = price_container.find('span', class_='a-price-whole')
                fraction = price_container.find('span', class_='a-price-fraction')
                if whole and fraction:
                    price_text = f"{whole.text.strip()}.{fraction.text.strip()}"
                    prices.append({'text': price_text})

            print(f"Found {len(product_titles)} products and {len(prices)} prices on Amazon")

            # Match products and prices
            for product, price in zip(product_titles, prices):
                try:
                    if isinstance(price, dict):
                        price_text = price['text']
                    else:
                        price_text = price.text.strip()
                    
                    # Clean and convert price
                    price_text = price_text.replace('$', '').replace(',', '')
                    price_value = float(price_text)
                    
                    if price_value > 0:
                        data.append({
                            'competitor': 'Amazon',
                            'product': product.text.strip(),
                            'price': price_value,
                            'timestamp': datetime.now()
                        })
                        
                except (ValueError, AttributeError) as e:
                    continue

            # Find next page link
            next_button = soup.find('a', {'class': 's-pagination-next'})
            next_url = urljoin(url, next_button['href']) if next_button else None
            return data, next_url
                
        except Exception as e:
            print(f"Error scraping Amazon page: {str(e)}")
            return data, None

    def scrape_bestbuy_page(self, url):
        data = []
        try:
            self.driver.get(url)
            time.sleep(7)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_containers = soup.find_all('div', class_='list-item')
            print(f"Found {len(product_containers)} products on BestBuy")

            for container in product_containers:
                try:
                    product = container.find('h4', class_='sku-title')
                    price_element = container.find('div', class_='priceView-customer-price')
                    if price_element:
                        price_span = price_element.find('span', {'aria-hidden': 'true'})
                        if price_span and product:
                            price_text = price_span.text.strip()
                            match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                            if match:
                                price_value = float(match.group(1).replace(',', ''))
                                if price_value > 0:
                                    data.append({
                                        'competitor': 'Bestbuy',
                                        'product': product.text.strip(),
                                        'price': price_value,
                                        'timestamp': datetime.now()
                                    })
                except (ValueError, AttributeError) as e:
                    continue

            next_button = soup.find('a', {'class': 'sku-list-page-next'})
            next_url = urljoin(url, next_button['href']) if next_button else None
            return data, next_url
        except Exception as e:
            print(f"Error scraping Best Buy page: {str(e)}")
            return data, None

    def scrape_walmart_page(self, url):
        data = []
        try:
            self.driver.get(url)
            time.sleep(5)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            product_elements = soup.find_all('span', attrs={'data-automation-id': 'product-title'})
            price_elements = soup.find_all('span', class_='w_iUH7')
            
            print(f"Found {len(product_elements)} products and {len(price_elements)} prices on Walmart")

            for product, price in zip(product_elements, price_elements):
                try:
                    price_text = price.text.strip().lower()
                    
                    if 'current price' in price_text:
                        price_text = price_text.replace('current price', '').strip()
                    elif 'now' in price_text:
                        price_text = price_text.split('now')[-1].strip()
                    elif 'was' in price_text:
                        continue
                        
                    match = re.search(r'\$(\d+(?:,\d{3})*\.?\d{0,2})', price_text)
                    if match:
                        price_str = match.group(1).replace(',', '')
                        price_value = float(price_str)
                        
                        if price_value > 0:
                            data.append({
                                'competitor': 'Walmart',
                                'product': product.text.strip(),
                                'price': price_value,
                                'timestamp': datetime.now()
                            })
                except (ValueError, AttributeError, IndexError) as e:
                    continue

            try:
                current_page = int(url.split('page=')[-1]) if 'page=' in url else 1
                next_url = f"{url}&page={current_page + 1}" if 'page=' in url else f"{url}&page=2"
                return data, next_url if data else None
            except:
                return data, None
                
        except Exception as e:
            print(f"Error scraping Walmart page: {str(e)}")
            return data, None

    def scrape_competitor_prices(self, competitor):
        all_data = []
        current_url = competitor['url']
        page = 1
        max_pages = 5  # Limit to prevent infinite loops

        while current_url and page <= max_pages:
            print(f"\nScraping {competitor['name']} - Page {page}...")
            
            if 'amazon' in competitor['url'].lower():
                data, next_url = self.scrape_amazon_page(current_url)
            elif 'bestbuy' in competitor['url'].lower():
                data, next_url = self.scrape_bestbuy_page(current_url)
            elif 'walmart' in competitor['url'].lower():
                data, next_url = self.scrape_walmart_page(current_url)
            
            if data:
                all_data.extend(data)
                print(f"Found {len(data)} products on page {page}")
            
            if not next_url:
                break
                
            current_url = next_url
            page += 1
            time.sleep(3)  # Wait between pages

        df = pd.DataFrame(all_data)
        if not df.empty:
            print(f"\nSuccessfully scraped total {len(df)} products from {competitor['name']}")
            print(f"Sample data:\n{df.head()}")
        else:
            print(f"No data was scraped from {competitor['name']}")
        
        return df

    def close(self):         
        self.driver.quit()