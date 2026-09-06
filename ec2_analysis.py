import json
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import boto3
from datetime import datetime

class AnalysisHandler(BaseHTTPRequestHandler):
    def send_headers(self, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()

    def do_POST(self):
        length_of_content = int(self.headers['Content-Length'])
        received_data = self.rfile.read(length_of_content)
        input_data = json.loads(received_data.decode('utf-8'))

        analysis_result = process_data(input_data)
        self.send_headers()
        self.wfile.write(json.dumps(analysis_result).encode('utf-8'))

def process_data(input_parameters):
    data = input_parameters['data']
    history_length = int(input_parameters['minhistory'])
    simulation_count = int(input_parameters['shots'])
    action_type = input_parameters['t']
    evaluation_period = int(input_parameters['p'])

    risk_assessment = evaluate_risk(data, history_length, simulation_count, action_type, evaluation_period)
    archive_results_s3(risk_assessment, action_type)
    
    return {'message': 'Risk analysis completed', 'details': risk_assessment}

def evaluate_risk(pricing_data, history_depth, simulations, risk_type, days_out):
    assessed_risks = []
    for index in range(history_depth, len(pricing_data)):
        if pricing_data[index][risk_type.capitalize()] == 1:
            historic_prices = [pricing_data[j]['Close'] for j in range(index - history_depth, index)]
            price_returns = [(p - historic_prices[k - 1]) / historic_prices[k - 1] for k, p in enumerate(historic_prices) if k > 0]
            avg_return = sum(price_returns) / len(price_returns)
            volatility = (sum((x - avg_return) ** 2 for x in price_returns) / len(price_returns)) ** 0.5

            simulated_values = sorted([random.gauss(avg_return, volatility) for _ in range(simulations)], reverse=True)
            risk_at_95 = simulated_values[int(len(simulated_values) * 0.05)]
            risk_at_99 = simulated_values[int(len(simulated_values) * 0.01)]
            assessed_risks.append({'var95': risk_at_95, 'var99': risk_at_99})

    return assessed_risks

def archive_results_s3(risks, type_of_risk):
    s3_storage = boto3.resource('s3')
    bucket = 'specified-s3-bucket-name'
    ec2_id = fetch_instance_id()
    file_name = f"{type_of_risk}{ec2_id}{datetime.now().isoformat()}.json"
    s3_storage.Object(bucket, file_name).put(Body=json.dumps({'evaluated_risks': risks}))

def fetch_instance_id():
    try:
        ec2 = boto3.client('ec2')
        response = ec2.describe_instances(InstanceIds=[ec2.meta.endpoint_url])
        if response['Reservations']:
            return response['Reservations'][0]['Instances'][0]['InstanceId']
    except Exception as error:
        print(f"Failed to retrieve instance ID: {str(error)}")
        return 'UnknownInstanceId'

def initiate_server(handler_class=AnalysisHandler, port=80):
    server_settings = ('', port)
    server = HTTPServer(server_settings, handler_class)
    print(f"Server is active on port {port}")
    server.serve_forever()

if _name_ == "_main_":
    initiate_server()
