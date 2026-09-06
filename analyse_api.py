# Function for invoking the Lambda Function (AWS)
import json
import random
from datetime import datetime

def lambda_handler(event, context):
    # Parsing JSON from event object, supporting different payload formats
    if 'body' in event:
        event = json.loads(event['body'])
    elif isinstance(event, str):
        event = json.loads(event)

    # Extracting the parameters from the event
    data = event.get('data', [])  # List of stock data dictionaries
    minhistory = int(event.get('h', 101))  # Window size for past data analysis
    shots = int(event.get('d', 10000))  # Number of Monte Carlo simulations
    transaction_type = event.get('t', 'buy').capitalize()  # Transaction type, 'Buy' or 'Sell'
    check_days = int(event.get('p', 7))  # Days ahead to calculate profit or loss

    results = []
    total_profit_loss = 0
    total_var95 = 0
    total_var99 = 0

    # Function to calculate mean of a list
    def calculate_mean(data):
        return sum(data) / len(data)
    
    # Function to calculate standard deviation of a list
    def calculate_std(data, mean):
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        return variance ** 0.5

    # Processing each data point if data is available
    if data:
        for i in range(minhistory, len(data)):
            signal = data[i][transaction_type]  # Extracting signal based on transaction type
            if signal == 1:  # Checking if the signal is a buy/sell action
                close_prices = [data[j]['Close'] for j in range(i - minhistory, i)]
                returns = [(close_prices[k] - close_prices[k - 1]) / close_prices[k - 1] for k in range(1, len(close_prices))]
                mean = calculate_mean(returns)
                std = calculate_std(returns, mean)

                simulated = [random.gauss(mean, std) for _ in range(shots)]
                simulated.sort()
                var95 = simulated[int(len(simulated) * 0.05)]
                var99 = simulated[int(len(simulated) * 0.01)]
                total_var95 += var95
                total_var99 += var99

                future_index = i + check_days  # Index for future price comparison
                profit_loss = None
                if future_index < len(data):
                    future_price = data[future_index]['Close']
                    current_price = data[i]['Close']
                    profit_loss = (future_price - current_price) / current_price if current_price else None
                    total_profit_loss += profit_loss if profit_loss else 0

                results.append({
                    'signal_date': data[i]['Date'],  # Recording the date of the signal
                    'var95': var95,
                    'var99': var99,
                    'profit_loss': profit_loss,
                    'type': transaction_type
                })

    # Computing averages for audit purposes
    count_signals = len(results)
    average_var95 = total_var95 / count_signals if count_signals else 0
    average_var99 = total_var99 / count_signals if count_signals else 0

    # Compiling final response
    response = {
        'results': results,
        'average_var95': average_var95,
        'average_var99': average_var99,
        'total_profit_loss': total_profit_loss,
        'timestamp': datetime.now().isoformat()
    }

    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }
