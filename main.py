from waitress import serve
from flask import Flask, jsonify, request, send_from_directory
import requests


class ScanGPTPlugin:

  # Define the constructor for the class
  def __init__(self, base_url, api_key):
    # Initialize the base_url attribute
    self.base_url = base_url
    self.api_key = api_key

  def get_tokens_balance(self, account_id, token_id):
    # Define the endpoint for the balance API
    endpoint = "/addresses/holdTokens"

    # Construct the full URL for the API request
    url = f"{self.base_url}{endpoint}?address={account_id}&network=ethereum"

    balance_info = self.query_mirror_node_for(url)

    if balance_info is not None:

      # Iterate over the 'balances' in the response data
      for item in balance_info.get('list', []):

        
        # Check if the token ID matches the requested token
        if item['symbol'] == token_id:

          # Get the number of decimals for the token
          decimals = float(item['decimal'])

          # Calculate the token balance and return it
          tBalance = float(item['count']) / (10**decimals)

          return tBalance

      # Return None if the query is wrong or if the account or token was not found
      return None

  def query_mirror_node_for(self, url):
    # Make a GET request to the mirror node REST API
    headers = {'auth-key': self.api_key}
    
    info = requests.get(url, headers=headers)
    # Check if the response status code is 200 (OK)
    if info.status_code == 200:
      # Parse the token info JSON response data
      info_data = info.json()
      return info_data
    else:
      # Return None if mirror node query is wrong or unsuccessful
      return None


# Initialize the plugin with the mainnet base URL
plugin = ScanGPTPlugin("https://knn3-gateway.knn3.xyz/data-api/api", "API Key from KNN3")

# Create the Flask web server
app = Flask(__name__)


@app.route('/get_tokens_balance', methods=['GET'])
def get_tokens_balance():
  # Use query parameter 'account_id' to specify the account ID
  account_id = request.args.get('account_id', '')
  token_id = request.args.get('token_id', '')
  token_balance = plugin.get_tokens_balance(account_id, token_id)
  if token_balance is not None:
    return jsonify({'account_id': account_id, 'token_balance': token_balance})
  else:
    return jsonify({
      'error':
      'Could not get the token balance for this account. Please check again.'
    }), 404


@app.route("/.well-known/ai-plugin.json", methods=['GET'])
def serve_ai_plugin():
  return send_from_directory(app.root_path,
                             'ai-plugin.json',
                             mimetype='application/json')


@app.route("/openapi.yaml", methods=['GET'])
def serve_openapi_yaml():
  return send_from_directory(app.root_path,
                             'openapi.yaml',
                             mimetype='text/yaml')


if __name__ == "__main__":
  serve(app, host="0.0.0.0", port=5000)

