# backend/app.py - Full Version with RAG, OpenAI FC (Password, Weather, Currency)
import os
import traceback 
import re 
import json # For parsing function arguments
import secrets # For password generation
import string  # For password generation
import requests # For weather & currency API calls
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI # Use the OpenAI library
from flask_cors import CORS 

# Attempt to import from data_store, define dummies if not found
try:
    # Define functions needed for intent detection or potential RAG (currently unused in main flow)
    from data_store import get_faq_answer, find_product, get_order_info, retrieve_product_info
    print("Functions from data_store imported.")
except ImportError as e:
    print(f"Warning: Could not import from data_store.py ({e}). Define dummy functions.")
    def get_faq_answer(q): return None
    def find_product(q): return None
    # Ensure get_order_info is defined even as dummy if schema exists later
    def get_order_info(order_id): return None 
    def retrieve_product_info(q): return None

load_dotenv() # Load environment variables from .env file

# --- OpenAI API Client Initialization ---
openai_api_key = os.getenv('OPENAI_API_KEY') 
openai_client = None
if openai_api_key:
    try:
        openai_client = OpenAI(api_key=openai_api_key) 
        print("OpenAI API Key configured and Client initialized.") 
    except Exception as e:
        print(f"Error initializing OpenAI client: {e}")
        openai_client = None
else:
    print("Warning: OPENAI_API_KEY not found in .env file.")
# --- End OpenAI Client Initialization ---


# --- Helper Function Implementations ---

def generate_random_password(length: int, include_symbols: bool = True) -> str:
    """Generates a secure random password of a specified length."""
    print(f"--- Function: generate_random_password(length={length}, include_symbols={include_symbols}) called ---")
    characters = string.ascii_letters + string.digits 
    if include_symbols:
        characters += string.punctuation
    try:
        length = int(length) 
        if length < 8: length = 8
        if length > 128: length = 128
    except (ValueError, TypeError):
         print(f"Warning: Non-integer length requested ({length}). Setting length to 12.")
         length = 12 
    try:
        password = ''.join(secrets.choice(characters) for i in range(length))
        print(f"--- Generated password (length {len(password)}): [Hidden] ---") 
        return password
    except Exception as e:
        print(f"!!! Error generating password: {e}")
        return "Error: Could not generate password due to an internal issue."

def get_current_weather(location: str, unit: str = "metric") -> str:
    """Gets the current weather for a specified location using OpenWeatherMap API."""
    print(f"--- Function: get_current_weather(location='{location}', unit='{unit}') called ---")
    api_key = os.getenv("OPENWEATHERMAP_API_KEY") 
    if not api_key:
        return "Error: Weather API key is not configured."

    units = "imperial" if unit and unit.lower() == "imperial" else "metric"
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = { "q": location, "appid": api_key, "units": units, "lang": "en" }

    try:
        api_response = requests.get(base_url, params=params, timeout=10) 
        api_response.raise_for_status() 
        data = api_response.json() 

        if data.get("cod") != 200 and data.get("message"): 
             return f"Error from weather API: {data['message']}" 

        main_data = data.get("main")
        weather_data = data.get("weather")[0] if data.get("weather") else {}
        city_name = data.get("name")
        country = data.get("sys", {}).get("country")

        if not main_data or not weather_data or not city_name:
            return f"Error: Could not parse weather data for {location}."

        temp = main_data.get("temp")
        feels_like = main_data.get("feels_like")
        humidity = main_data.get("humidity")
        description = weather_data.get("description")
        temp_unit = "°F" if units == "imperial" else "°C" 
        location_display = f"{city_name}, {country}" if country else city_name

        result_str = (
            f"The current weather in {location_display} is {description}. "
            f"The temperature is {temp}{temp_unit} (feels like {feels_like}{temp_unit}). "
            f"Humidity is {humidity}%."
        )
        print(f"--- Formatted weather result: {result_str}")
        return result_str

    except requests.exceptions.Timeout: return f"Error: The weather service request timed out."
    except requests.exceptions.HTTPError as http_err:
         print(f"!!! HTTP error occurred: {http_err}")
         if api_response.status_code == 404: return f"Error: Could not find weather data for '{location}'. Check spelling."
         elif api_response.status_code == 401: return "Error: Invalid Weather API key."
         else: return f"Error fetching weather ({api_response.status_code})."
    except requests.exceptions.RequestException as req_err: return f"Error connecting to weather service: {req_err}"
    except Exception as e:
         print(f"!!! Unexpected error in get_current_weather: {e}")
         traceback.print_exc() 
         return "Error: Unexpected error fetching weather."

def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Converts a specified amount from one currency to another using ExchangeRate-API."""
    print(f"--- Function: convert_currency(amount={amount}, from={from_currency}, to={to_currency}) called ---")
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
        return "Error: Currency conversion API key is not configured."

    try: amount_float = float(amount)
    except (ValueError, TypeError): return "Error: Invalid amount provided. Please provide a number."
    
    from_curr = str(from_currency).upper()
    to_curr = str(to_currency).upper()
    if not (len(from_curr) == 3 and from_curr.isalpha() and len(to_curr) == 3 and to_curr.isalpha()):
         return "Error: Please use valid 3-letter ISO 4217 currency codes (e.g., USD, JPY)."

    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{from_curr}/{to_curr}/{amount_float}"
    safe_url_log = f"{url[:url.find(api_key) + len(api_key[:5])]}...{url[url.find('/pair'):]}"
    print(f"Calling ExchangeRate-API: {safe_url_log}") 

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data.get("result") == "success":
            conversion_result = data.get("conversion_result")
            if conversion_result is not None:
                result_str = f"{amount_float:.2f} {from_curr} is approximately {conversion_result:.2f} {to_curr}."
                print(f"--- Formatted conversion result: {result_str}")
                return result_str
            else: return "Error: Could not get conversion result from API."
        elif data.get("result") == "error":
            error_type = data.get("error-type", "Unknown API error")
            print(f"!!! Error from ExchangeRate-API: {error_type}")
            if error_type == "invalid-key": return "Error: Invalid Currency API key."
            elif error_type == "inactive-account": return "Error: Currency API account inactive."
            elif error_type == "unsupported-code": return f"Error: Unsupported currency code ({from_curr} or {to_curr})."
            else: return f"Error during currency conversion: {error_type}"
        else: return "Error: Unexpected response from currency service."

    except requests.exceptions.Timeout: return f"Error: Currency service request timed out."
    except requests.exceptions.HTTPError as http_err: return f"Error fetching exchange rates ({response.status_code})."
    except requests.exceptions.RequestException as req_err: return f"Error connecting to currency service: {req_err}"
    except Exception as e:
         print(f"!!! Unexpected error in convert_currency: {e}")
         traceback.print_exc() 
         return "Error: Unexpected error during currency conversion."
# --- End Helper Functions ---


# --- Function Calling Schema Definition ---
available_tools = None 
try:
    generate_password_func_declaration = {
        "name": "generate_random_password", 
        "description": "Generates a secure random password with a specified length, optionally including symbols.", 
        "parameters": { "type": "object", "properties": { "length": {"type": "integer", "description": "Desired length (8-128)."}, "include_symbols": {"type": "boolean", "description": "Include symbols? Defaults true."}}, "required": ["length"] }
    }
    get_current_weather_func_declaration = {
        "name": "get_current_weather", 
        "description": "Get the current weather conditions for a specified location.", 
        "parameters": { "type": "object", "properties": { "location": {"type": "string", "description": "City/Location (e.g., 'Tokyo', 'Brisbane, AU')."}, "unit": {"type": "string", "description": "'metric' (C) or 'imperial' (F). Defaults metric.", "enum": ["metric", "imperial"]}}, "required": ["location"] }
    }
    convert_currency_func_declaration = {
        "name": "convert_currency", 
        "description": "Convert an amount from one currency to another using real-time rates.",
        "parameters": { "type": "object", "properties": { "amount": {"type": "number", "description": "Amount to convert."}, "from_currency": {"type": "string", "description": "3-letter currency code FROM (e.g., 'USD')."}, "to_currency": {"type": "string", "description": "3-letter currency code TO (e.g., 'JPY')."} }, "required": ["amount", "from_currency", "to_currency"] }
    }
    # List of tools for OpenAI API
    available_tools = [
        {"type": "function", "function": generate_password_func_declaration},
        {"type": "function", "function": get_current_weather_func_declaration},
        {"type": "function", "function": convert_currency_func_declaration}
    ]
    print(f"Function calling tools prepared successfully for: {[tool.get('function', {}).get('name', 'Unknown') for tool in available_tools]}") 
except Exception as e_dict_schema:
    print(f"!!! Error defining dictionary schema or tools list: {e_dict_schema}")
    available_tools = None
if available_tools is None: print("Warning: `available_tools` could not be defined. Function Calling will be skipped.")
# --- End Function Calling Schema Definition ---


# --- Flask App Setup ---
app = Flask(__name__)
CORS(app) # Enable CORS
# --- End Flask App Setup ---


# --- Routes ---
@app.route('/')
def hello():
    return "React+OpenAI Chatbot Backend is running!"

# --- Main Chat Route (Handles Function Calling for Password, Weather, Currency) ---
@app.route('/chat', methods=['POST'])
def chat():
    print("--- /chat endpoint called ---")
    status_code = 500
    response_data = {"error": "An unexpected internal error occurred."} 

    try:
        data = request.get_json()
        print(f"Received data: {data}")
        if not data or 'query' not in data:
            return jsonify({"error": "Request body must contain 'query'."}), 400

        user_query = data['query'].strip()
        print(f"User query: '{user_query}'")

        if not openai_client:
             response_data = {"error": "AI Client (OpenAI) not initialized."}
             return jsonify(response_data), 500

        # --- Prepare for API Call ---
        messages = [{"role": "user", "content": user_query}]
        use_tools_flag = bool(available_tools) # Check if tools were defined successfully

        if use_tools_flag:
            print(f"Attempting OpenAI call WITH TOOLS for query: '{user_query}'")
            try:
                # === First API Call: Send query and tools ===
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini", 
                    messages=messages,
                    tools=available_tools, 
                    tool_choice="auto" 
                )
                response_message = response.choices[0].message 
                messages.append(response_message) 
                print("OpenAI initial response received.")

                # === Check for Tool Calls ===
                tool_calls = response_message.tool_calls 
                
                if tool_calls:
                    print(f"Tool calls requested: {len(tool_calls)}")
                    available_functions = {
                        "generate_random_password": generate_random_password,
                        "get_current_weather": get_current_weather,
                        "convert_currency": convert_currency
                    }
                    
                    # --- Execute local functions ---
                    for tool_call in tool_calls:
                        function_name = tool_call.function.name
                        function_args_str = tool_call.function.arguments
                        tool_call_id = tool_call.id 
                        print(f"-> Function Call Requested: {function_name}")
                        print(f"-> Arguments (raw string): {function_args_str}")
                        
                        function_to_call = available_functions.get(function_name)
                            
                        if function_to_call:
                            function_response = None # Initialize for safety
                            try:
                                function_args = json.loads(function_args_str)
                                print(f"Parsed arguments: {function_args}") 

                                # Prepare kwargs safely
                                call_kwargs = {} 
                                if function_name == "generate_random_password":
                                    length = function_args.get("length")
                                    include_symbols = function_args.get("include_symbols") 
                                    if length is not None: call_kwargs["length"] = int(length)
                                    if include_symbols is not None and isinstance(include_symbols, bool): call_kwargs["include_symbols"] = include_symbols
                                elif function_name == "get_current_weather":
                                    location = function_args.get("location")
                                    unit = function_args.get("unit") 
                                    if location: call_kwargs["location"] = str(location)
                                    else: raise ValueError("'location' argument required")
                                    if unit is not None: call_kwargs["unit"] = str(unit) 
                                elif function_name == "convert_currency":
                                    amount = function_args.get("amount")
                                    from_currency = function_args.get("from_currency")
                                    to_currency = function_args.get("to_currency")
                                    if amount is not None: call_kwargs["amount"] = float(amount)
                                    else: raise ValueError("'amount' argument required")
                                    if from_currency and len(str(from_currency)) == 3: call_kwargs["from_currency"] = str(from_currency).upper()
                                    else: raise ValueError("'from_currency' required (3-letter code)")
                                    if to_currency and len(str(to_currency)) == 3: call_kwargs["to_currency"] = str(to_currency).upper()
                                    else: raise ValueError("'to_currency' required (3-letter code)")

                                print(f"Calling local function: {function_name} with args: {call_kwargs}")
                                function_response = function_to_call(**call_kwargs) 
                                print(f"Local function '{function_name}' response generated.")
                            
                            # Catch errors during arg parsing/validation or function execution
                            except (json.JSONDecodeError, ValueError, TypeError) as arg_err: 
                                 print(f"!!! Argument/Type Error for {function_name}: {arg_err}")
                                 function_response = f"Error: Invalid arguments provided - {str(arg_err)}"
                            except Exception as e_func_call: 
                                 print(f"!!! Error executing local function {function_name}: {e_func_call}")
                                 traceback.print_exc()
                                 function_response = f"Error executing function: {str(e_func_call)}"
                            
                            # Append result (or error string) to messages
                            messages.append(
                                { "tool_call_id": tool_call_id, "role": "tool", "name": function_name, "content": function_response }
                            )
                        else:
                            # Function not found
                            print(f"!!! Warning: Function '{function_name}' requested but not implemented.")
                            messages.append({"tool_call_id": tool_call_id, "role": "tool", "name": function_name, "content": f"Error: Function '{function_name}' not available."})

                    # === Second API Call ===
                    print("Calling OpenAI again with tool results...")
                    try:
                        response_final = openai_client.chat.completions.create( model="gpt-4o-mini", messages=messages )
                        message_final = response_final.choices[0].message
                        response_text = message_final.content if message_final.content else "(AI had no further response)"
                        status_code = 200
                        print("OpenAI final response received.")
                    except Exception as e_openai_2:
                         print(f"!!! OpenAI API call error (2nd call): {e_openai_2}")
                         response_text = f"Error communicating with AI after tool use: {str(e_openai_2)}"
                         status_code = 500 
                         
                else:
                    # --- No tool call requested ---
                    print("No tool call requested by AI. Using initial response.")
                    response_text = response_message.content if response_message.content else "(AI returned an empty response)"
                    status_code = 200 # Still a successful interaction

                # Prepare final response data
                if status_code == 200: response_data = {"response": response_text}
                else: response_data = {"error": response_text} 
                
                print(f"Final response text determined: {response_text}")
                return jsonify(response_data), status_code

            except Exception as e_fc_outer:
                # Catch errors during the main FC try block
                print(f"!!! Error during Function Calling process: {e_fc_outer}")
                traceback.print_exc()
                response_data = {"error": f"An error occurred during AI processing with tools: {str(e_fc_outer)}"}
                return jsonify(response_data), 500

        # --- Fallback to General Chat IF available_tools was None ---
        else: 
             print("--- Handling as General Chat (Function Calling Tools Unavailable) ---")
             # ... (Existing simple chat completion logic) ...
             try:
                 # ... (Call OpenAI, get response_text) ...
                 status_code = 200
                 response_data = {"response": response_text}
             except Exception as e_gen_chat:
                 # ... (Handle error) ...
                 status_code = 500
                 response_data = {"error": ...}
             return jsonify(response_data), status_code

    except Exception as e_very_outer:
         # Catch-all for unexpected errors (e.g., request.get_json() fails)
         print(f"!!! Unexpected error in chat function top level: {e_very_outer}")
         traceback.print_exc()
         return jsonify({"error": "An unexpected internal error occurred."}), 500
# --- End Chat Route ---

# --- Server Start ---
if __name__ == '__main__':
    print(">>> Starting Flask server via app.run()...")
    app.run(debug=True, host='0.0.0.0', port=5000) 
# --- End Server Start ---