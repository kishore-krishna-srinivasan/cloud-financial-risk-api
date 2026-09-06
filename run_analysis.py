# Analysis Script for EC2 (using SSM and S3)

import pandas as pd
import numpy as np
import json
import random
from datetime import datetime
import boto3

# Function to calculate statistical analysis for trading signals
def calculate_analysis(data, h, d, t, p):
    minhistory = h  # minimum history required for the analysis
    shots = d       # number of simulation shots for Monte Carlo method
    transaction_type = t  # 'Buy' or 'Sell'
    check_days = p  # days after the transaction date to check price difference

    results_list = []
    total_profit_loss = 0
    total_var95 = 0
    total_var99 = 0

    # Function to calculate mean of a dataset
    def calculate_mean(data):
        return sum(data) / len(data)

    # Function to calculate standard deviation of a dataset
    def calculate_std(data, mean):
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5

    if not data.empty:
        # Processing each entry in the data
        for i in range(minhistory, len(data)):
            signal = data.at[i, transaction_type]
            if signal == 1:
                close_prices = [data.at[j, 'Close'] for j in range(i - minhistory, i)]
                returns = [(close_prices[k] - close_prices[k - 1]) / close_prices[k - 1] for k in range(1, len(close_prices))]
                mean = calculate_mean(returns)
                std = calculate_std(returns, mean)

                # Monte Carlo simulations to calculate VaR
                simulated = [random.gauss(mean, std) for _ in range(shots)]
                simulated.sort()
                var95 = simulated[int(len(simulated) * 0.05)]
                var99 = simulated[int(len(simulated) * 0.01)]
                total_var95 += var95
                total_var99 += var99

                # Calculating the profit or loss
                future_index = i + check_days
                if future_index < len(data):
                    future_price = data.at[future_index, 'Close']
                    current_price = data.at[i, 'Close']
                    profit_loss = (future_price - current_price) / current_price if current_price else None
                    total_profit_loss += profit_loss if profit_loss else 0

                results_list.append({
                    'signal_date': data.at[i, 'Date'],
                    'var95': var95,
                    'var99': var99,
                    'profit_loss': profit_loss,
                    'type': transaction_type
                })

    count_signals = len(results_list)
    average_var95 = total_var95 / count_signals if count_signals else 0
    average_var99 = total_var99 / count_signals if count_signals else 0

    return {
        'results': results_list,
        'average_var95': average_var95,
        'average_var99': average_var99,
        'total_profit_loss': total_profit_loss,
        'timestamp': datetime.now().isoformat()
    }

# Function to handle events and context
def handler(event, context):
    data = pd.read_json(event['data'])
    h = event['h']
    d = event['d']
    t = event['t']
    p = event['p']

    results = calculate_analysis(data, h, d, t, p)
    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
