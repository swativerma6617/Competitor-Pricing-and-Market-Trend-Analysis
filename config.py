# config.py
import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'OPENAI_API_KEY': os.getenv('OPEN_API_KEY'),
    'DATABASE_URL': os.getenv('DATABASE_URL'),
    'COMPETITORS': [
        {'name': 'Amazon', 'url': 'https://www.amazon.com/laptops'},
        {'name': 'Bestbuy', 'url': 'https://www.bestbuy.com/site/laptop-computers/all-laptops/pcmcat138500050001.c'},
        {'name': 'Walmart', 'url': 'https://www.walmart.com/browse/electronics/laptops/3944_3951_1089430'}
        
    ],
    'UPDATE_FREQUENCY': 24,  # hours
    'PRICE_THRESHOLD': 0.05  # 5% price change threshold
}