from src.data_collection import WebScraper
from src.data_preprocessor import DataPreprocessor
from src.price_analyzer import PriceAnalyzer
import pandas as pd
import time
from config import CONFIG

def main():
    # Initialize components
    scraper = WebScraper(CONFIG)
    preprocessor = DataPreprocessor(CONFIG)
    analyzer = PriceAnalyzer(CONFIG)
    
    def job():
        try:
            # Collect data
            print("\nStarting data collection...")
            all_data = pd.DataFrame()
            
            for competitor in CONFIG['COMPETITORS']:
                print(f"\nScraping data from {competitor['name']}...")
                data = scraper.scrape_competitor_prices(competitor)
                
                # Debug print
                print(f"Data collected from {competitor['name']}:")
                print(f"Columns: {data.columns.tolist() if not data.empty else 'No data'}")
                print(f"Shape: {data.shape}")
                
                if not data.empty:
                    all_data = pd.concat([all_data, data], ignore_index=True)
            
            # Debug print
            print("\nCombined data:")
            print(f"Columns: {all_data.columns.tolist() if not all_data.empty else 'No data'}")
            print(f"Shape: {all_data.shape}")
            
            if not all_data.empty:
                # Process data
                print("\nCleaning data...")
                clean_data = preprocessor.clean_price_data(all_data)
                preprocessor.save_to_database(clean_data, 'competitor_prices')
                
                # Analyze price changes
                """"
                print("\nAnalyzing price changes...")
                price_changes = analyzer.detect_price_changes(clean_data)
                if not price_changes.empty:
                    insights = analyzer.analyze_market_trends(price_changes)
                    print("\nMarket Insights:", insights)
            else:
                print("\nNo data was collected from any competitor.") """
                
        except Exception as e:
            print(f"\nError in job: {str(e)}")
            import traceback
            print(traceback.format_exc())
    
    try:
        # Run once
        job()
    finally:
        scraper.close()
        print("\nProcess completed.")

if __name__ == "__main__":
    main()
