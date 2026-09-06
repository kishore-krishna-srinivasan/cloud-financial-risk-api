import json
import boto3
from datetime import datetime, timedelta

def lambda_handler(event, context):
    # Initialize AWS Cost Explorer Client
    cost_explorer = boto3.client('ce', region_name='us-east-1')
    
    # Calculate the time period for which costs are to be calculated
    today = datetime.utcnow()
    start_date, end_date = calculate_date_range(today)
    
    # Set up the filter based on tagging to identify specific resources
    cost_filter = create_tag_filter('Coursework', 'WarmupFunc')
    
    # Retrieve the cost data from AWS Cost Explorer
    cost_data = fetch_cost_data(cost_explorer, start_date, end_date, cost_filter)
    
    # Calculate the total cost from the retrieved data
    total_cost = sum_costs(cost_data)
    
    # Prepare the response with billable time and total cost
    return prepare_response(24, total_cost)  # Assumes 24 hours in a day

def calculate_date_range(base_date):
    """Returns the start and end dates as strings formatted for AWS Cost Explorer."""
    end_date = base_date.strftime('%Y-%m-%d')
    start_date = (base_date - timedelta(days=1)).strftime('%Y-%m-%d')
    return start_date, end_date

def create_tag_filter(tag_key, tag_value):
    """Creates a filter dictionary for querying costs based on a specific tag."""
    return {
        'Tags': {
            'Key': tag_key,
            'Values': [tag_value]
        }
    }

def fetch_cost_data(cost_explorer_client, start_date, end_date, cost_filter):
    """Fetches cost data from AWS Cost Explorer."""
    try:
        response = cost_explorer_client.get_cost_and_usage(
            TimePeriod={'Start': start_date, 'End': end_date},
            Granularity='DAILY',
            Metrics=["UnblendedCost"],
            Filter=cost_filter
        )
        return response['ResultsByTime']
    except Exception as e:
        print(f"Error fetching cost data: {e}")
        raise

def sum_costs(cost_data):
    """Sums up the unblended costs from the cost data."""
    return sum(float(day['Total']['UnblendedCost']['Amount']) for day in cost_data)

def prepare_response(billable_hours, total_cost):
    """Prepares the final JSON response containing the billing information."""
    return {
        'statusCode': 200,
        'body': json.dumps({'billable_time': billable_hours, 'cost': total_cost})
    }

