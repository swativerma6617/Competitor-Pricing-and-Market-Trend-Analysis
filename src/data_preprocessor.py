import pandas as pd
from sqlalchemy import create_engine, text
import time

class DataPreprocessor:
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.setup_database()

    def setup_database(self):
        """Setup database connection with retry logic"""
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                print("Attempting database connection...")
                self.engine = create_engine(self.config['DATABASE_URL'])

                # Test the connection - Update this part
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))  # Use text() to wrap SQL strings
                print("Database connection successful!")
                return

            except Exception as e:
                retry_count += 1
                print(f"Database connection attempt {retry_count} failed: {str(e)}")
                if retry_count < max_retries:
                    time.sleep(2)  # Wait before retrying
                else:
                    print("Could not connect to database after multiple attempts")
                    raise

    def clean_price_data(self, df):
        # Clean the price column
        df['price'] = df['price'].apply(self._clean_price)

        # Remove outliers
        df = df[df['price'] > 0]

        # Handle missing values
        df = df.dropna()

        # Convert timestamps to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        return df

    def _clean_price(self, price_str):
        """Clean price string to proper float format"""
        try:
            # Remove currency symbols and commas
            price_str = str(price_str).replace('$', '').replace(',', '')
            # Handle case where there might be multiple decimals
            if price_str.count('.') > 1:
                parts = price_str.split('.')
                price_str = parts[0] + '.' + parts[1]
            return float(price_str)
        except (ValueError, TypeError):
            return 0.0

    def save_to_database(self, df, table_name):
        """Save data to database with error handling"""
        try:
            if self.engine is None:
                print("No database connection. Attempting to reconnect...")
                self.setup_database()

            if not df.empty:
                df.to_sql(table_name, self.engine, if_exists='append',
                         index=False, chunksize=500)
                print(f"Successfully saved {len(df)} records to database")
            else:
                print("No data to save to database")

        except Exception as e:
            print(f"Error saving to database: {str(e)}")
            # Save to CSV as backup
            backup_file = f"backup_{table_name}_{int(time.time())}.csv"
            df.to_csv(backup_file, index=False)
            print(f"Data backed up to {backup_file}")

    def load_from_database(self, query):
        return pd.read_sql(query, self.engine)