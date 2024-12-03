# src/analysis/price_analyzer.py
"""""
import pandas as pd
import numpy as np
from openai import OpenAI

class PriceAnalyzer:
    def __init__(self, config):
        self.client = OpenAI(api_key=config['OPENAI_API_KEY'])
        self.threshold = config['PRICE_THRESHOLD']
    
    def detect_price_changes(self, df):
        # Group by product and competitor
        grouped = df.groupby(['competitor', 'product'])
        
        price_changes = []
        for (competitor, product), group in grouped:
            group = group.sort_values('timestamp')
            
            # Calculate price changes
            pct_change = group['price'].pct_change()
            significant_changes = pct_change.abs() >= self.threshold
            
            if significant_changes.any():
                price_changes.append({
                    'competitor': competitor,
                    'product': product,
                    'change': pct_change[significant_changes].iloc[-1],
                    'timestamp': group['timestamp'][significant_changes].iloc[-1]
                })
        
        return pd.DataFrame(price_changes)
    
    def analyze_market_trends(self, price_changes_df):
        # Prepare market trend analysis for GPT
        trend_description = price_changes_df.to_string()
        
        response = self.client.chat.completions.create(
            model="gpt-4",
            messages=[{
                "role": "system",
                "content": "Analyze the following price changes and provide strategic insights:"
            }, {
                "role": "user",
                "content": trend_description
            }]
        )
        
        return response.choices[0].message.content """