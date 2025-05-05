# AI Chatbot MVP (React + Flask + OpenAI)

## Overview

This is the second Minimum Viable Product (MVP) portfolio project, building upon previous experience. It's a web-based chatbot application demonstrating practical integration between a modern frontend (**React** with Vite) and a Python/Flask backend powered by the **OpenAI API (GPT models)**.

The chatbot is designed to act as a simple task assistant, capable of:
* Generating secure random passwords.
* Fetching real-time weather information for a specified location.
* Converting currency amounts between specified currencies.
* Engaging in general conversation for other requests.

This project utilizes **Function Calling** via the OpenAI API to understand user intent for specific tasks and execute corresponding backend functions.

## Demo (Optional but Recommended)

*(ここに、アプリケーションが動作している様子の短いGIFアニメーションや動画へのリンクを挿入)*
*(Placeholder: Insert a short GIF or video link demonstrating the application in action)*

`![Chatbot Demo GIF](assets/demo_react_openai.gif)` *(<- ファイル名は例です)*

## Features

* **Conversational Interface:** Simple, responsive chat UI built with **React**, displaying conversation history clearly. Includes loading and error indicators.
* **Task Execution (Function Calling):**
    * Utilizes **OpenAI API's Function Calling** capability.
    * Identifies user requests for specific tasks (password generation, weather check, currency conversion).
    * Extracts necessary parameters (e.g., password length, location, amount, currencies) from the user's natural language query.
    * Calls corresponding backend Python functions via API request.
    * **Implemented Tools:**
        * `generate_random_password`: Creates secure random passwords using Python's `secrets` module.
        * `get_current_weather`: Fetches real-time weather data from the OpenWeatherMap API.
        * `convert_currency`: Converts currencies using the ExchangeRate-API.com API.
    * Generates a natural language response based on the function's execution result.
* **General Conversation:** Falls back to standard OpenAI API generation (instructed for English responses) for queries that don't trigger a function call.

## Tech Stack

* **Frontend:** **React (v18+)**, Vite, Axios, CSS
* **Backend:** **Python (v3.11+)**, **Flask**, **`openai` (Python library)**, `python-dotenv`, `Flask-CORS`, `requests`
* **AI Model:** **OpenAI API (GPT-4o-mini or GPT-3.5-turbo)**
* **External APIs:** OpenWeatherMap API, ExchangeRate-API.com API
* **Development:** Git, GitHub, Virtual Environment (`.venv`), pip, npm, VS Code

## Key Implementations & Learnings

This project focused on implementing multi-tool Function Calling with the OpenAI API and building the frontend with React.

### OpenAI Function Calling Implementation

1.  Defined clear schemas (in dictionary format) for three distinct functions (`generate_random_password`, `get_current_weather`, `convert_currency`) describing their purpose and parameters.
2.  Passed these schemas to the OpenAI API (`gpt-4o-mini`) using the `tools` parameter in the `chat.completions.create` method.
3.  Implemented backend logic (`app.py`) to:
    * Check the API response for `tool_calls`.
    * Parse the function name and arguments (JSON string) requested by the AI.
    * Map the function name to the corresponding local Python implementation.
    * Safely execute the local Python function with the parsed arguments (including type validation).
    * Package the function's return value into a `tool` role message with the correct `tool_call_id`.
    * Send the updated conversation history (including the `tool` message) back to the OpenAI API for final response generation.
4.  This demonstrates a robust way to give LLMs access to external tools and real-time information.

### React Frontend Basics

* Built the UI using functional components and hooks (`useState`, `useRef`, `useEffect`).
* Managed application state (input message, chat history, loading status).
* Handled user input and button clicks to trigger asynchronous API calls (`axios`) to the Flask backend.
* Implemented dynamic rendering of the chat history using `.map()`.
* Added basic loading and error message indicators.
* Utilized CSS for layout and styling, including fixing scroll behavior.

### Challenges & Learnings

* Learning React fundamentals (JSX, state, props, effects) coming from Vue.js.
* Understanding the specific request/response structure and history format required for OpenAI's Function Calling implementation (compared to Gemini's).
* Integrating and handling responses/errors from multiple external APIs (OpenWeatherMap, ExchangeRate-API).
* Debugging the end-to-end flow involving Frontend -> Backend -> OpenAI API -> Backend Function -> OpenAI API -> Backend -> Frontend.
* Implementing robust argument parsing and validation for function calls initiated by the LLM.

## Setup and Usage (Local)

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yskmtb0714/chatbot-react-openai.git
    cd chatbot-react-openai
    ```
2.  **Backend Setup:**
    * Navigate to `backend`: `cd backend`
    * Create venv: `python -m venv .venv`
    * Activate venv: `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (Windows)
    * Install dependencies: `pip install -r requirements.txt`
    * Create `.env` file in `backend` directory.
    * Add your keys to `.env`:
        ```dotenv
        OPENAI_API_KEY='YOUR_OPENAI_API_KEY'
        OPENWEATHERMAP_API_KEY='YOUR_OPENWEATHERMAP_API_KEY'
        EXCHANGERATE_API_KEY='YOUR_EXCHANGERATE_API_KEY'
        ```
3.  **Frontend Setup:**
    * Navigate to `frontend`: `cd ../frontend`
    * Install dependencies: `npm install`
4.  **Run the Application:**
    * **Terminal 1 (Backend):** `cd backend`, activate venv, `python app.py`
    * **Terminal 2 (Frontend):** `cd frontend`, `npm run dev`
5.  **Access:** Open the `Local:` URL (e.g., `http://localhost:5173/`) in your browser.