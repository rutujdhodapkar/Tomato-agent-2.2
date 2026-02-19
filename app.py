import base64
import io
import json
import os
import re
from datetime import datetime
import time

import requests
import streamlit as st
from PIL import Image
from streamlit_js_eval import streamlit_js_eval

# ================= CONFIG ================= #
# API key intentionally kept in-code per requirement.
OPENROUTER_API_KEY = "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"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "nvidia/nemotron-nano-12b-v2-vl:free"
VISION_MODEL = "nvidia/nemotron-nano-12b-v2-vl:free"
REASONING_MODEL = "openai/gpt-oss-120b:free"
FALLBACK_MODELS = [
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "google/gemini-flash-1.5-8b:free"
]
FARM_CONTEXT_FILE = "farm_context.json"
USER_DB = "users.json"
EXPORT_DIR = "exports"
REPORTS_DIR = "reports"
os.makedirs(REPORTS_DIR, exist_ok=True)

# ================= LANGUAGE / FONT ================= #
TRANSLATIONS = {
    "English": {
        "home": "Home",
        "chat": "Chat",
        "shops": "Shop",
        "doctors": "Doctors",
        "contact": "Contact",
        "username": "Username",
        "password": "Password",
        "upload": "Upload Leaf Image",
        "analyze": "Analyze",
        "btn_desc": "📄 Disease Description",
        "btn_sol": "💡 Get Solution",
        "btn_fert": "🧪 Get Fertilizers",
    },
    "Hindi": {
        "home": "होम",
        "chat": "चैट",
        "shops": "दुकान",
        "doctors": "डॉक्टर्स",
        "contact": "संपर्क",
        "username": "यूज़रनेम",
        "password": "पासवर्ड",
        "upload": "पत्ता अपलोड करें",
        "analyze": "विश्लेषण",
        "btn_desc": "📄 बीमारी का विवरण",
        "btn_sol": "💡 समाधान प्राप्त करें",
        "btn_fert": "🧪 उर्वरक प्राप्त करें",
    },
    "Marathi": {
        "home": "मुख्यपृष्ठ",
        "chat": "चॅट",
        "shops": "दुकान",
        "doctors": "डॉक्टर्स",
        "contact": "संपर्क",
        "username": "वापरकर्ता नाव",
        "password": "पासवर्ड",
        "upload": "पान अपलोड करा",
        "analyze": "विश्लेषण",
        "btn_desc": "📄 रोगाचे वर्णन",
        "btn_sol": "💡 उपाय मिळवा",
        "btn_fert": "🧪 खते मिळवा",
    },
}
FONT_MAP = {
    "English": "Arial, sans-serif",
    "Hindi": "'Nirmala UI', 'Mangal', sans-serif",
    "Marathi": "'Noto Sans Devanagari', 'Mangal', sans-serif",
}



NAV_ICONS = {
    "home": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M21.4498 10.275L11.9998 3.1875L2.5498 10.275L2.9998 11.625H3.7498V20.25H20.2498V11.625H20.9998L21.4498 10.275ZM5.2498 18.75V10.125L11.9998 5.0625L18.7498 10.125V18.75H14.9999V14.3333L14.2499 13.5833H9.74988L8.99988 14.3333V18.75H5.2498ZM10.4999 18.75H13.4999V15.0833H10.4999V18.75Z" fill="#FFFFFF"></path> </g></svg>""",
    "chat": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M8 10.5H16" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"></path> <path d="M8 14H13.5" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"></path> <path d="M17 3.33782C15.5291 2.48697 13.8214 2 12 2C6.47715 2 2 6.47715 2 12C2 13.5997 2.37562 15.1116 3.04346 16.4525C3.22094 16.8088 3.28001 17.2161 3.17712 17.6006L2.58151 19.8267C2.32295 20.793 3.20701 21.677 4.17335 21.4185L6.39939 20.8229C6.78393 20.72 7.19121 20.7791 7.54753 20.9565C8.88837 21.6244 10.4003 22 12 22C17.5228 22 22 17.5228 22 12C22 10.1786 21.513 8.47087 20.6622 7" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round"></path> </g></svg>""",
    "shops": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M3 10V19C3 20.1046 3.89543 21 5 21H19C20.1046 21 21 20.1046 21 19V10" stroke="#FFFFFF" stroke-width="1.5"></path> <path d="M14.8333 21V15C14.8333 13.8954 13.9379 13 12.8333 13H10.8333C9.72874 13 8.83331 13.8954 8.83331 15V21" stroke="#FFFFFF" stroke-width="1.5" stroke-miterlimit="16"></path> <path d="M21.8183 9.36418L20.1243 3.43517C20.0507 3.17759 19.8153 3 19.5474 3H15.5L15.9753 8.70377C15.9909 8.89043 16.0923 9.05904 16.2532 9.15495C16.6425 9.38698 17.4052 9.81699 18 10C19.0158 10.3125 20.5008 10.1998 21.3465 10.0958C21.6982 10.0526 21.9157 9.7049 21.8183 9.36418Z" stroke="#FFFFFF" stroke-width="1.5"></path> <path d="M14 10C14.5675 9.82538 15.2879 9.42589 15.6909 9.18807C15.8828 9.07486 15.9884 8.86103 15.9699 8.63904L15.5 3H8.5L8.03008 8.63904C8.01158 8.86103 8.11723 9.07486 8.30906 9.18807C8.71207 9.42589 9.4325 9.82538 10 10C11.493 10.4594 12.507 10.4594 14 10Z" stroke="#FFFFFF" stroke-width="1.5"></path> <path d="M3.87567 3.43517L2.18166 9.36418C2.08431 9.7049 2.3018 10.0526 2.6535 10.0958C3.49916 10.1998 4.98424 10.3125 6 10C6.59477 9.81699 7.35751 9.38698 7.74678 9.15495C7.90767 9.05904 8.00913 8.89043 8.02469 8.70377L8.5 3H4.45258C4.18469 3 3.94926 3.17759 3.87567 3.43517Z" stroke="#FFFFFF" stroke-width="1.5"></path> </g></svg>""",
    "doctors": """<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path d="M12 1.25C12.4142 1.25 12.75 1.58579 12.75 2V2.25143C12.8612 2.25311 12.9561 2.25675 13.0446 2.26458C14.8548 2.42465 16.2896 3.85953 16.4497 5.66968C16.4643 5.83512 16.4643 6.02256 16.4643 6.29785L16.4643 7.521C16.4643 11.3903 13.5202 14.5719 9.75001 14.9481V17.0001C9.75001 19.3473 11.6528 21.2501 14 21.2501H14.8824C16.2803 21.2501 17.4809 20.3981 17.9902 19.1822C18.03 19.0872 18.0578 18.9789 18.075 18.8547C16.8708 18.4647 16 17.3341 16 16C16 14.3431 17.3432 13 19 13C20.6569 13 22 14.3431 22 16C22 17.4603 20.9567 18.6768 19.5748 18.945C19.5472 19.2085 19.4887 19.4872 19.3738 19.7617C18.6391 21.5156 16.9058 22.7501 14.8824 22.7501H14C10.8244 22.7501 8.25001 20.1757 8.25001 17.0001V14.9495C4.3217 14.5722 1.25001 11.2625 1.25001 7.23529L1.25 6.29791C1.24997 6.02259 1.24995 5.83514 1.26458 5.66968C1.42465 3.85953 2.85954 2.42465 4.66969 2.26458C4.82536 2.25081 5.00051 2.25002 5.25001 2.24999V2C5.25001 1.58579 5.58579 1.25 6.00001 1.25C6.41422 1.25 6.75001 1.58579 6.75001 2V4C6.75001 4.41421 6.41422 4.75 6.00001 4.75C5.58579 4.75 5.25001 4.41421 5.25001 4V3.75002C4.9866 3.7502 4.88393 3.75148 4.80181 3.75875C3.71573 3.85479 2.85479 4.71572 2.75875 5.80181C2.75074 5.8924 2.75001 6.00802 2.75001 6.3369V7.23529C2.75001 10.6871 5.54823 13.4853 9.00001 13.4853C12.294 13.4853 14.9643 10.815 14.9643 7.521V6.3369C14.9643 6.00802 14.9636 5.8924 14.9555 5.80181C14.8595 4.71572 13.9986 3.85479 12.9125 3.75875C12.8702 3.755 12.8224 3.75285 12.75 3.75162V4C12.75 4.41421 12.4142 4.75 12 4.75C11.5858 4.75 11.25 4.41421 11.25 4V2C11.25 1.58579 11.5858 1.25 12 1.25Z" fill="#FFFFFF"></path> </g></svg>""",
    "contact": """<svg viewBox="0 -0.5 25 25" fill="none" xmlns="http://www.w3.org/2000/svg"><g id="SVGRepo_bgCarrier" stroke-width="0"></g><g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g><g id="SVGRepo_iconCarrier"> <path fill-rule="evenodd" clip-rule="evenodd" d="M14.5 11.5C14.5 12.6046 13.6046 13.5 12.5 13.5C11.3954 13.5 10.5 12.6046 10.5 11.5C10.5 10.3954 11.3954 9.5 12.5 9.5C13.6046 9.5 14.5 10.3954 14.5 11.5Z" stroke="#FFFFFF" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"></path> <path d="M14.5 5.25C14.0858 5.25 13.75 5.58579 13.75 6C13.75 6.41421 14.0858 6.75 14.5 6.75V5.25ZM10.5 6.75C10.9142 6.75 11.25 6.41421 11.25 6C11.25 5.58579 10.9142 5.25 10.5 5.25V6.75ZM15.25 6C15.25 5.58579 14.9142 5.25 14.5 5.25C14.0858 5.25 13.75 5.58579 13.75 6H15.25ZM13.75 7C13.75 7.41421 14.0858 7.75 14.5 7.75C14.9142 7.75 15.25 7.41421 15.25 7H13.75ZM13.75 6C13.75 6.41421 14.0858 6.75 14.5 6.75C14.9142 6.75 15.25 6.41421 15.25 6H13.75ZM15.25 4C15.25 3.58579 14.9142 3.25 14.5 3.25C14.0858 3.25 13.75 3.58579 13.75 4H15.25ZM14.5 6.75C14.9142 6.75 15.25 6.41421 15.25 6C15.25 5.58579 14.9142 5.25 14.5 5.25V6.75ZM10.5 5.25C10.0858 5.25 9.75 5.58579 9.75 6C9.75 6.41421 10.0858 6.75 10.5 6.75V5.25ZM11.25 6C11.25 5.58579 10.9142 5.25 10.5 5.25C10.0858 5.25 9.75 5.58579 9.75 6H11.25ZM9.75 7C9.75 7.41421 10.0858 7.75 10.5 7.75C10.9142 7.75 11.25 7.41421 11.25 7H9.75ZM9.75 6C9.75 6.41421 10.0858 6.75 10.5 6.75C10.9142 6.75 11.25 6.41421 11.25 6H9.75ZM11.25 4C11.25 3.58579 10.9142 3.25 10.5 3.25C10.0858 3.25 9.75 3.58579 9.75 4H11.25ZM6.05108 17.8992C5.71926 18.1471 5.65126 18.6171 5.89919 18.9489C6.14713 19.2807 6.61711 19.3487 6.94892 19.1008L6.05108 17.8992ZM18.0511 19.1008C18.3829 19.3487 18.8529 19.2807 19.1008 18.9489C19.3487 18.6171 19.2807 18.1471 18.9489 17.8992L18.0511 19.1008ZM14.5 6.75H15.5V5.25H14.5V6.75ZM15.5 6.75C17.2949 6.75 18.75 8.20507 18.75 10H20.25C20.25 7.37665 18.1234 5.25 15.5 5.25V6.75ZM18.75 10V16H20.25V10H18.75ZM18.75 16C18.75 17.7949 17.2949 19.25 15.5 19.25V20.75C18.1234 20.75 20.25 18.6234 20.25 16H18.75ZM15.5 19.25H9.5V20.75H15.5V19.25ZM9.5 19.25C7.70507 19.25 6.25 17.7949 6.25 16H4.75C4.75 18.6234 6.87665 20.75 9.5 20.75V19.25ZM6.25 16V10H4.75V16H6.25ZM6.25 10C6.25 8.20507 7.70507 6.75 9.5 6.75V5.25C6.87665 5.25 4.75 7.37665 4.75 10H6.25ZM9.5 6.75H10.5V5.25H9.5V6.75ZM13.75 6V7H15.25V6H13.75ZM15.25 6V4H13.75V6H15.25ZM14.5 5.25H10.5V6.75H14.5V5.25ZM9.75 6V7H11.25V6H9.75ZM11.25 6V4H9.75V6H11.25ZM6.94892 19.1008C10.2409 16.641 14.7591 16.641 18.0511 19.1008L18.9489 17.8992C15.1245 15.0416 9.87551 15.0416 6.05108 17.8992L6.94892 19.1008Z" fill="#FFFFFF"></path> </g></svg>""",
}


def reverse_geocode(lat, lon):
    """Converts lat/lon to a readable location string using Nominatim."""
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
        headers = {"User-Agent": "AgriSuperAgent/1.0"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            address = data.get("address", {})
            city = address.get("city") or address.get("town") or address.get("village") or address.get("suburb")
            state = address.get("state")
            country = address.get("country")
            parts = [p for p in [city, state, country] if p]
            return ", ".join(parts) if parts else f"{lat}, {lon}"
    except Exception:
        pass
    return f"{lat}, {lon}"


def get_ip_location():
    """Fetches rough location based on user's IP as a fallback."""
    try:
        response = requests.get("https://ipapi.co/json/", timeout=5)
        if response.status_code == 200:
            data = response.json()
            city = data.get("city")
            region = data.get("region")
            country = data.get("country_name")
            parts = [p for p in [city, region, country] if p]
            return ", ".join(parts) if parts else None
    except Exception:
        pass
    return None


def get_svg_base64(svg_str):
    return base64.b64encode(svg_str.encode()).decode()


def call_openrouter(messages, model=REASONING_MODEL):
    """Calls OpenRouter with a fallback mechanism."""
    models_to_try = [model] + [m for m in FALLBACK_MODELS if m != model]
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    last_error = ""
    retry_delay = 2 # Start with 2s delay for 429s

    for i, current_model in enumerate(models_to_try):
        payload = {"model": current_model, "messages": messages}
        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            
            # If 429 (Rate Limit), wait and try next or retry
            if response.status_code == 429:
                last_error = f"Model {current_model} rate limited (429). Waiting {retry_delay}s..."
                time.sleep(retry_delay)
                retry_delay *= 2 # Exponential backoff
                continue

            # If 404, try next model
            if response.status_code == 404:
                last_error = f"Model {current_model} failed with 404. Trying fallback..."
                continue
                
            if response.status_code != 200:
                last_error = f"HTTP Error {response.status_code}: {response.text}"
                continue

            if "application/json" not in response.headers.get("Content-Type", ""):
                last_error = f"API returned non-JSON response from {current_model}"
                continue

            data = response.json()
            if "choices" in data:
                content = data["choices"][0]["message"]["content"]
                
                # Check for textual refusals inside a successful 200 response
                refusal_keywords = ["i am sorry", "i'm sorry", "i cannot provide", "i can't provide", "i am an ai", "as an ai model"]
                if any(kw in content.lower() for kw in refusal_keywords):
                    last_error = f"Model {current_model} refused: {content[:100]}..."
                    continue
                
                return content

            if "error" in data:
                last_error = f"API Error ({current_model}): {data['error'].get('message')}"
                continue
                
            last_error = f"Unexpected format from {current_model}: {data}"
        except requests.exceptions.RequestException as e:
            last_error = f"Network Error ({current_model}): {str(e)}"
            continue

    return last_error or "All models failed."


def save_farm_context(data):
    """Saves farm context (location, disease, crop) to JSON."""
    try:
        with open(FARM_CONTEXT_FILE, "w") as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving farm context: {e}")

def load_farm_context():
    """Loads farm context from JSON."""
    if os.path.exists(FARM_CONTEXT_FILE):
        try:
            with open(FARM_CONTEXT_FILE, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}


def _fetch_submodel_data(prompt, label, location):
    """Generic submodel fetcher with robust JSON extraction."""
    response = call_openrouter([{"role": "user", "content": prompt}])
    
    # 🔥 Check if response is an error message from call_openrouter
    if any(err_sig in response for err_sig in ["HTTP Error", "API Error", "Network Error", "Unexpected format", "refused"]):
        return None, response

    try:
        clean_json = response.strip()
        
        # 1. Try markdown extraction
        if "```json" in clean_json:
            clean_json = clean_json.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_json:
            clean_json = clean_json.split("```")[1].split("```")[0].strip()
            
        # 2. Try regex to find the JSON block (Look for the first '{' and corresponding last '}')
        if not (clean_json.startswith("{") or clean_json.startswith("[")):
            match = re.search(r'(\{.*\}|\[.*\])', clean_json, re.DOTALL)
            if match:
                clean_json = match.group(0)

        data = json.loads(clean_json)
        
        # Validation: Check if it's just a placeholder failure
        summary_text = str(data).lower()
        if any(kw in summary_text for kw in ["unavailable", "could not fetch"]):
            return None, "Data quality insufficient (placeholder returned)"
            
        return data, None
    except Exception as e:
        return None, f"JSON Parse Error: {str(e)} | Raw: {response[:100]}..."

def agricultural_intelligence_orchestrator(location, status_callback):
    """
    The Main Model: Orchestrates 6 Sub-Models (Weather, Climate, Soil, Irrigation, Market, Pest Risk).
    Retries until valid data is fetched for all layers.
    """
    reports = {
        "weather": None, "climate": None, "soil": None,
        "irrigation": None, "market": None, "pest_risk": None
    }
    
    # Detailed Prompts for Sub-Models
    prompts = {
        "weather": f"""As a specialized agricultural assistant, provide a COMPREHENSIVE 3-year weather trend report for {location}. 
        Include: 
        1. Annual Rainfall (mm) for the last 3 years.
        2. Average Temperature range (Min/Max) per season.
        3. Extreme Event History (Droughts, Floods, Heatwaves).
        4. Planting Window Advice based on trends.
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts).""",
        
        "climate": f"""As a specialized agricultural assistant, provide a LIVE climate Status for {location}.
        Include:
        1. Current Soil Moisture % estimate.
        2. 7-Day Rainfall Forecast (Daily mm).
        3. Humidity and Evapotranspiration rates.
        4. Frost or Heat Stress alerts.
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts).""",
        
        "soil": f"""As a specialized agricultural assistant, provide a REGIONAL Soil Health Survey for {location}.
        Include:
        1. N-P-K Levels (Nitrogen, Phosphorus, Potassium) estimate.
        2. Soil pH and Organic Carbon content.
        3. Micronutrients (Zinc, Boron, Iron) status.
        4. Soil Texture (Silt, Clay, Sand) and Drainage quality.
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts).""",

        "irrigation": f"""As a specialized agricultural assistant, provide an IRRIGATION & WATER report for {location}.
        Include:
        1. Primary Water Source status (Well, River, Canal).
        2. Seasonal Water Availability forecast.
        3. Recommended Irrigation Method (Drip, Sprinkler) for Tomato.
        4. Dialy Watering Schedule (Liters per plant estimate).
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts).""",

        "market": f"""As a specialized agricultural assistant, provide a MARKET & ECONOMIC analysis for Tomato in {location}.
        Include:
        1. Current Local Market Price (per kg) estimate.
        2. Price Trend (Rising/Stable/Falling).
        3. Nearby Cold Storage or Processing Units.
        4. Export Potential and Variety Demand (Cherry, Roma, Beefsteak).
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts).""",

        "pest_risk": f"""As a specialized agricultural assistant, provide a PEST & BIOSECURITY risk report for {location}.
        Include:
        1. Top 5 local Tomato Pests/Diseases (e.g., Tuta Absoluta, Leaf Miner).
        2. Current regional outbreak risk (Low/Medium/High).
        3. Biological Control recommendations.
        4. Early Warning signs for farmers to watch.
        Output ONLY valid JSON with 'summary' (long text) and 'table_data' (list of dicts)."""
    }

    for layer in reports.keys():
        attempt = 0
        while reports[layer] is None and attempt < 10:
            attempt += 1
            status_callback(f"• Fetching {layer.replace('_', ' ').title()} data (Attempt {attempt}/10)...")
            
            data, err = _fetch_submodel_data(prompts[layer], layer, location)
            if data:
                reports[layer] = data
                status_callback(f"✅ {layer.replace('_', ' ').title()} data secured.")
                
                # Save to reports dir
                path = os.path.join(REPORTS_DIR, f"{layer}_{datetime.now().strftime('%Y%m%d')}.json")
                with open(path, "w") as f:
                    json.dump(data, f)
            else:
                status_callback(f"⚠️ {layer.replace('_', ' ').title()} fetch failed: {err}. Retrying...")
                time.sleep(2) 
        
        # Fallback if max retries reached
        if reports[layer] is None:
            status_callback(f"❌ Failed to secure {layer} data after 10 attempts. Using placeholder.")
            reports[layer] = {
                "summary": f"Maximum retries reached for {layer}. Using historical averages.",
                "table_data": [{"Metric": "Status", "Value": "Data Unavailable (Retry Limit)"}]
            }
    
    return reports


def run_reasoning_model(image_bytes, location, weather=None, climate=None, soil=None, irrigation=None, market=None, pest_risk=None, retry_count=0):
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Nudge if retry
    nudge = "IMPORTANT: Focus strictly on identifying if this is a TOMATO plant. If not, state clearly." if retry_count > 0 else ""

    prompt = f"""
    {nudge}
    Analyze this plant image and the following environmental reports for {location}.
    Weather Trends: {json.dumps(weather)}
    Climate Status: {json.dumps(climate)}
    Soil Health: {json.dumps(soil)}
    Irrigation/Water: {json.dumps(irrigation)}
    Market Analysis: {json.dumps(market)}
    Pest/Disease Risk: {json.dumps(pest_risk)}

    Role: Specialized Tomato Pathologist.
    
    Requirement:
    1. Verify if the plant is a Tomato. If it is NOT a tomato, set 'crop_name' to 'Not Tomato'.
    2. If it is a Tomato, provide:
       - Precise Disease Diagnosis.
       - Short-term action (Next 7 Days).
       - Mid-term plan (Next 1 Month).
       - Long-term strategy (Next 3 Months).
       - Recommended fertilizers with estimated costs (₹).

    Return ONLY valid JSON in this structure:
    {{
        "crop_name": "Tomato" or "Not Tomato",
        "disease_name": "...",
        "diagnosis_details": "...",
        "plan_7_days": "...",
        "plan_1_month": "...",
        "plan_3_months": "...",
        "fertilizers": [
            {{"name": "...", "cost": "...", "reason": "..."}}
        ],
        "risk_score": "Low/Medium/High"
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
    


    if "application/json" not in response.headers.get("Content-Type", ""):
        return {"error": "API returned non-JSON response", "raw": response.text[:500]}

    try:
        result = response.json()
    except requests.exceptions.JSONDecodeError:
         return {"error": "Failed to decode JSON", "raw": response.text[:500]}

    if "choices" not in result:
        err_msg = "Unknown error"
        if "error" in result:
            err_msg = result["error"].get("message", "Unknown error")
        return {"error": f"API Error: {err_msg}", "raw_response": result}

    try:
        output_text = result["choices"][0]["message"]["content"].strip()
        
        # 1. Try markdown extraction
        if "```json" in output_text:
            output_text = output_text.split("```json")[1].split("```")[0].strip()
        elif "```" in output_text:
            output_text = output_text.split("```")[1].split("```")[0].strip()
            
        # 2. Try regex as robust fallback
        if not (output_text.startswith("{") or output_text.startswith("[")):
            match = re.search(r'(\{.*\}|\[.*\])', output_text, re.DOTALL)
            if match:
                output_text = match.group(0)

        return json.loads(output_text)
    except Exception as e:
        return {"error": f"Reasoning model failed to parse output: {str(e)}", "raw_content": output_text if 'output_text' in locals() else str(result)}


def run_soil_intelligence_model(location, weather=None, soil=None):
    """
    Synthesizes soil and weather data to provide improvement insights.
    """
    prompt = f"""
    Analyze the following environmental context for {location} to provide SOIL IMPROVEMENT and FERTILIZER advice.
    Weather/Climate Trends: {json.dumps(weather)}
    Current Soil Health: {json.dumps(soil)}

    Role: Expert Agricultural Soil Scientist.

    Objective:
    1. Analyze current soil deficiencies based on N-P-K, pH, and weather conditions.
    2. Provide detailed actions to make the soil "more better" and productive.
    3. Recommend specific fertilizers and biological inputs for maximum output.
    4. Consider weather timing (e.g., nitrogen application relative to rain).

    Return ONLY valid JSON in this structure:
    {{
        "soil_status": "Brief summary of soil health",
        "deficiencies": ["List of main issues"],
        "improvement_actions": ["Detailed step-by-step actions"],
        "fertilizer_recommendations": [
            {{"name": "...", "reason": "...", "cost": "...", "timing": "Best time to apply"}}
        ],
        "weather_impact": "How current weather affects soil management",
        "yield_forecast": "Potential output improvement estimate"
    }}
    """

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": REASONING_MODEL,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        output_text = response.json()["choices"][0]["message"]["content"].strip()
        
        # Robust extraction
        if "```json" in output_text:
            output_text = output_text.split("```json")[1].split("```")[0].strip()
        elif "```" in output_text:
            output_text = output_text.split("```")[1].split("```")[0].strip()
        if not (output_text.startswith("{") or output_text.startswith("[")):
            match = re.search(r'(\{.*\}|\[.*\])', output_text, re.DOTALL)
            if match: output_text = match.group(0)

        return json.loads(output_text)
    except Exception as e:
        return {"error": f"Soil Intelligence model failed: {str(e)}", "raw": output_text if 'output_text' in locals() else "Unknown"}


def ensure_session_defaults():
    defaults = {
        "language": "English",
        "chat_history": [],
        "detection_result": None,
        "menu_choice": "Home",
        "location": "",
        "pending_shop_query": None,
        "last_weather": None,
        "last_climate": None,
        "last_soil": None,
        "last_irrigation": None,
        "last_market": None,
        "last_pest_risk": None,
        "analysis_mode": "Disease Detection",
        "manual_n": "Medium", # Low/Medium/High
        "manual_p": "Medium",
        "manual_k": "Medium",
        "manual_ph": "6.5",
        "manual_moisture": "20.0",
        "manual_rainfall": "0.0",
        "soil_analysis_result": None
    }
    
    # Load persistent context
    ctx = load_farm_context()
    if ctx:
        if ctx.get("location"): defaults["location"] = ctx["location"]
        if ctx.get("disease_name"): defaults["detected_disease"] = ctx["disease_name"]
        if ctx.get("crop_name"): defaults["detected_crop"] = ctx["crop_name"]

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_local_font(language):
    font_family = FONT_MAP.get(language, FONT_MAP["English"])
    st.markdown(
        f"""
        <style>
            # Navigation Button Styles
            [data-testid="stHorizontalBlock"] [data-testid="column"] button {{
                width: 100% !important;
                height: 48px !important;
                border: 1px solid rgba(255,255,255,0.1) !important;
                background-color: #1a1a1a !important;
                color: #888 !important;
                font-weight: 500 !important;
                font-size: 14px !important;
                background-repeat: no-repeat !important;
                background-position: 8px center !important;
                background-size: 20px 20px !important;
                padding-left: 36px !important;
                border-radius: 8px !important;
                margin: 0 !important;
            }}
            .stApp {{
                margin-top: -50px !important;
            }}
            #main-content {{
                padding-top: 50px !important;
            }}
            
            @import url('https://fonts.googleapis.com/css2?family={font_family.replace(" ", "+")}&display=swap');
            
            html, body, [data-testid="stAppViewContainer"] {{
                font-family: '{font_family}', sans-serif !important;
            }}
            
            /* Fertilizer Card Styling */
            .fert-card {{
                background-color: #f0f7f4;
                border-left: 5px solid #2e7d32;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 15px;
                box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
            }}
            .fert-title {{
                color: #1b5e20;
                font-weight: bold;
                font-size: 1.1em;
                margin-bottom: 5px;
            }}
            .fert-cost {{
                color: #d32f2f;
                font-weight: bold;
                font-size: 0.9em;
            }}
            .fert-reason {{
                color: #455a64;
                font-size: 0.95em;
                margin-top: 5px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Inject dynamic icons for buttons based on position
    icon_styles = ""
    menu_keys = ["home", "chat", "shops", "doctors", "contact"]
    for i, key in enumerate(menu_keys):
        b64 = get_svg_base64(NAV_ICONS[key])
        icon_styles += f"""
        header + div [data-testid="stHorizontalBlock"] [data-testid="column"]:nth-of-type({i+1}) button {{
            background-image: url("data:image/svg+xml;base64,{b64}") !important;
        }}
        """
    
    st.markdown(f"<style>{icon_styles}</style>", unsafe_allow_html=True)


def sidebar_controls(lang_text):
    with st.sidebar:
        st.title("🤖 Agent Control Panel")

        # 1. Mode Selection
        st.session_state.analysis_mode = st.radio(
            "Select Purpose",
            ["Disease Detection", "Soil Intelligence"],
            index=0 if st.session_state.analysis_mode == "Disease Detection" else 1
        )
        st.markdown("---")
        # Language selection with Apply button
        current_lang_idx = list(TRANSLATIONS.keys()).index(st.session_state.language)
        new_lang = st.selectbox("Select Language", list(TRANSLATIONS.keys()), index=current_lang_idx)
        
        if st.button("Apply Language"):
            st.session_state.language = new_lang
            st.rerun()


def home_page(lang_text):
    st.markdown("# 🌱 Welcome to Tomato Detection System!")
    st.markdown("### Your ultimate companion for tomato planting, care, and disease management.")
    st.markdown("""
    **Use the Tomato System to:**
    - Detect and diagnose diseases in tomato plants.
    - Get expert advice and treatment options with Planty AI.
    - Shop for high-quality fertilizers, pesticides, and seeds.
    """)
    st.markdown("---")

    # ---------- LOCATION AUTO-FETCH ----------
    # Try GPS first
    loc = streamlit_js_eval(data_of='get_location', key='live_location')
    
    if loc and not st.session_state.location:
        lat = loc.get('coords', {}).get('latitude')
        lon = loc.get('coords', {}).get('longitude')
        if lat and lon:
            st.session_state.location = reverse_geocode(lat, lon)
            save_farm_context({
                "location": st.session_state.location,
                "disease_name": st.session_state.get("detected_disease", ""),
                "crop_name": st.session_state.get("detected_crop", "Tomato")
            })
    
    # Fallback to IP if still empty
    if not st.session_state.location:
        st.session_state.location = get_ip_location() or ""
        if st.session_state.location:
            save_farm_context({
                "location": st.session_state.location,
                "disease_name": st.session_state.get("detected_disease", ""),
                "crop_name": st.session_state.get("detected_crop", "Tomato")
            })

    # Show text box only if not fetched
    if not st.session_state.location:
        st.warning("📍 Location unavailable. Please enter manually.")
        st.session_state.location = st.text_input("Enter farm location", value="")

    # ---------- ANALYSIS LOGIC ----------
    if st.session_state.analysis_mode == "Disease Detection":
        st.markdown("### 📸 Disease Diagnosis")
        uploaded_image = st.file_uploader(lang_text["upload"], type=["jpg", "jpeg", "png"], label_visibility="collapsed")

        if uploaded_image:
            image = Image.open(uploaded_image)
            st.image(image, caption="Uploaded Leaf", use_container_width=True)
            
            if st.button(lang_text["analyze"]):
                buffer = io.BytesIO()
                image.save(buffer, format="JPEG")
                img_bytes = buffer.getvalue()
                
                status_container = st.empty()
                with status_container.container():
                    st.markdown("### 🔁 Running full farm intelligence pipeline...")
                    
                    # Use the Orchestrator (Main Model) for sub-models
                    reports = agricultural_intelligence_orchestrator(
                        st.session_state.location, 
                        lambda msg: st.write(msg)
                    )
                    
                    st.session_state.last_weather = reports["weather"]
                    st.session_state.last_climate = reports["climate"]
                    st.session_state.last_soil = reports["soil"]
                    st.session_state.last_irrigation = reports["irrigation"]
                    st.session_state.last_market = reports["market"]
                    st.session_state.last_pest_risk = reports["pest_risk"]
                    
                    st.write("• Analyzing image & synthesizing all reports…")
                    
                    # RETRY LOOP for Tomato Detection
                    final_result = None
                    for attempt in range(3):
                        if attempt > 0:
                            st.write(f"• Retrying tomato verification (Attempt {attempt+1}/3)…")
                        
                        result = run_reasoning_model(
                            img_bytes, 
                            st.session_state.location,
                            weather=st.session_state.last_weather,
                            climate=st.session_state.last_climate,
                            soil=st.session_state.last_soil,
                            irrigation=st.session_state.last_irrigation,
                            market=st.session_state.last_market,
                            pest_risk=st.session_state.last_pest_risk,
                            retry_count=attempt
                        )
                    
                        if "error" in result:
                            final_result = result
                            break
                        
                        if result.get("crop_name") == "Tomato":
                            final_result = result
                            # Save to context
                            st.session_state.detected_disease = result.get("disease_name")
                            st.session_state.detected_crop = "Tomato"
                            save_farm_context({
                                "location": st.session_state.location,
                                "disease_name": st.session_state.detected_disease,
                                "crop_name": st.session_state.detected_crop
                            })
                            break
                        else:
                            final_result = result # Keep the 'Not Tomato' result if last attempt
                            time.sleep(1)
                
                status_container.empty()
                st.session_state.detection_result = final_result
            
            if final_result and "error" not in final_result:
                if final_result.get("crop_name") == "Tomato":
                    st.success("Tomato Farm Intelligence Report Generated!")
                else:
                    st.warning("⚠️ High confidence that this is not a Tomato plant. No diagnosis provided.")
                st.rerun()
            else:
                st.error(final_result.get("error", "Unknown Error") if final_result else "No result.")

    else: # Soil Intelligence Mode
        st.markdown("### 🧪 Soil Health & Optimization")
        st.write("Get professional insights on how to improve your soil based on location data or manual reports.")
        
        # --- Relocated Manual Entry ---
        with st.expander("📝 Manual Report Input (Override AI)") :
            col1, col2 = st.columns(2)
            with col1:
                st.session_state.manual_n = st.selectbox("Nitrogen (N)", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.manual_n))
                st.session_state.manual_p = st.selectbox("Phosphorus (P)", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.manual_p))
                st.session_state.manual_k = st.selectbox("Potassium (K)", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(st.session_state.manual_k))
            with col2:
                st.session_state.manual_ph = st.text_input("Soil pH", value=st.session_state.manual_ph)
                st.session_state.manual_moisture = st.text_input("Moisture %", value=st.session_state.manual_moisture)
                st.session_state.manual_rainfall = st.text_input("Rainfall (mm)", value=st.session_state.manual_rainfall)
            
            if st.button("📥 Apply Manual Override"):
                st.session_state.last_soil = {
                    "summary": "Manually entered soil data.",
                    "table_data": [
                        {"Metric": "Nitrogen", "Value": st.session_state.manual_n},
                        {"Metric": "Phosphorus", "Value": st.session_state.manual_p},
                        {"Metric": "Potassium", "Value": st.session_state.manual_k},
                        {"Metric": "pH", "Value": st.session_state.manual_ph}
                    ]
                }
                st.session_state.last_climate = {
                    "summary": "Manually entered climate data.",
                    "table_data": [
                        {"Metric": "Soil Moisture", "Value": f"{st.session_state.manual_moisture}%"},
                        {"Metric": "Rainfall", "Value": f"{st.session_state.manual_rainfall}mm"}
                    ]
                }
                st.success("Manual data applied! You can now run Soil AI Analysis.")

        if st.button("🚀 Run Soil AI Analysis"):
            status_container = st.empty()
            with status_container.container():
                # 1. Fetch data if missing
                if not st.session_state.last_soil:
                    st.write("• Fetching regional reports...")
                    reports = agricultural_intelligence_orchestrator(st.session_state.location, lambda msg: st.write(msg))
                    st.session_state.last_weather = reports["weather"]
                    st.session_state.last_climate = reports["climate"]
                    st.session_state.last_soil = reports["soil"]
                
                st.write("• Synchronizing data with Soil Intelligence Model...")
                res = run_soil_intelligence_model(
                    st.session_state.location,
                    weather=st.session_state.last_weather,
                    soil=st.session_state.last_soil
                )
                st.session_state.soil_analysis_result = res
                status_container.empty()
                st.rerun()

        if st.session_state.soil_analysis_result:
            res = st.session_state.soil_analysis_result
            if "error" in res:
                st.error(res["error"])
            else:
                st.success("Soil Intelligence Report Ready!")
                st.markdown(f"## 🌾 {res.get('soil_status')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("#### ❌ Deficiencies Found")
                    for d in res.get("deficiencies", []):
                        st.write(f"• {d}")
                    
                    st.markdown("#### 🛠️ Improvement Actions")
                    for a in res.get("improvement_actions", []):
                        st.info(a)

                with col2:
                    st.markdown("#### 🧪 Fertilizer Advice")
                    for f in res.get("fertilizer_recommendations", []):
                        st.markdown(f"""
                        <div class="fert-card">
                            <div class="fert-title">🔬 {f.get('name')}</div>
                            <div class="fert-reason"><b>Timing:</b> {f.get('timing')}</div>
                            <div class="fert-reason"><b>Why:</b> {f.get('reason')}</div>
                            <div class="fert-cost">💰 Cost Est: {f.get('cost')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.warning(f"**⚡ Weather Impact:** {res.get('weather_impact')}")
                    st.metric("Estimated Yield Increase", res.get("yield_forecast", "N/A"))

                st.markdown("---")

    # ---------- RESULT DISPLAY (Above Uploader) ----------
    if st.session_state.detection_result and "error" not in st.session_state.detection_result:
        res = st.session_state.detection_result
        
        if res.get("crop_name") == "Tomato":
            st.markdown("---")
            st.markdown("## 🍅 Detailed Tomato Intelligence Report")
            
            st.markdown(f"### 🛑 Diagnosis: {res.get('disease_name', 'Healthy')}")
            st.write(res.get("diagnosis_details", "No details available."))

            st.markdown("### 📅 Treatment & Care Roadmap")
            # Visual Grid for Roadmap
            st.info(f"**🟢 NEXT 7 DAYS**\n\n{res.get('plan_7_days', 'N/A')}")
            st.warning(f"**🟡 NEXT 1 MONTH**\n\n{res.get('plan_1_month', 'N/A')}")
            st.error(f"**🔴 NEXT 3 MONTHS**\n\n{res.get('plan_3_months', 'N/A')}")

            st.markdown("---")
            st.markdown("### 🧪 Recommended Fertilizers & Solutions")
            ferts = res.get("fertilizers", [])
            search_terms = []
            if ferts:
                # Render as Visual Cards
                for f in ferts:
                    st.markdown(f"""
                    <div class="fert-card">
                        <div class="fert-title">🔬 {f.get('name')}</div>
                        <div class="fert-reason"><b>Usage:</b> {f.get('reason')}</div>
                        <div class="fert-cost">💰 Estimated Cost: {f.get('cost')}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    search_terms.append(f"{f.get('name')} price")
                
                st.write("") # Spacer
                if st.button("🛒 Shop Recommended Fertilizers Online"):
                    st.session_state.pending_shop_query = " + ".join(search_terms)
                    st.session_state.menu_choice = lang_text["shops"]
                    st.rerun()
            else:
                st.write("No specific fertilizers recommended.")

            st.markdown("---")
            st.markdown("### 📊 Background Intelligence Reports")
            
            def render_report_expander(icon, title, data_key):
                with st.expander(f"{icon} {title}"):
                    report = st.session_state.get(data_key)
                    if report and isinstance(report, dict):
                        st.markdown(f"#### Overview")
                        st.write(report.get("summary", "No summary provided."))
                        
                        table_data = report.get("table_data")
                        if table_data:
                            st.markdown("#### Structured Data")
                            st.table(table_data)
                    else:
                        st.write(f"No {title.lower()} data available.")

            render_report_expander("☁️", "Weather Trends (3y)", "last_weather")
            render_report_expander("💧", "Climate & Water Status", "last_climate")
            render_report_expander("🌱", "Local Soil Health", "last_soil")
            render_report_expander("🚿", "Irrigation & Schedules", "last_irrigation")
            render_report_expander("📈", "Market & Economics", "last_market")
            render_report_expander("🪲", "Pest & Biosecurity Risk", "last_pest_risk")

            st.markdown("---")
        else:
            st.error("🚫 Operation Interrupted: The system identified this image as a non-tomato plant. Diagnosis and treatment are restricted to tomatoes.")


def chat_page():
    st.title("💬 Agent Chat")
    
    # Chat container for scrollable messages
    chat_container = st.container()
    
    with chat_container:
        for msg in st.session_state.chat_history:
            with st.chat_message(msg['role']):
                st.markdown(f"*{msg['time']}*")
                st.write(msg['text'])

    query = st.chat_input("Ask about farming, costs, irrigation, market, disease...")
    if query:
        st.session_state.chat_history.append(
            {"time": datetime.now().strftime("%H:%M:%S"), "role": "user", "text": query}
        )
        with st.spinner("Agent is thinking..."):
            answer = call_openrouter(
                [
                    {"role": "system", "content": "You are a practical agricultural AI agent."},
                    {"role": "user", "content": query},
                ]
            )
        st.session_state.chat_history.append(
            {"time": datetime.now().strftime("%H:%M:%S"), "role": "assistant", "text": answer}
        )
        st.rerun()


def shop_or_doctors_page(title, actor, lang_text):
    st.title(title)
    
    # Check for redirected query
    initial_crop = ""
    initial_req = ""
    
    if actor == "Shop" and st.session_state.pending_shop_query:
        initial_req = st.session_state.pending_shop_query
        st.session_state.pending_shop_query = None # Clear after use
        st.info(f"Searching for recommended products: {initial_req}")

    col_in1, col_in2 = st.columns(2)
    with col_in1:
        # Integrated context: Only show requirement for both Shop and Doctors
        st.write(f"📍 Location: **{st.session_state.location or 'Auto-fetching...'}**")
        if st.session_state.get("detected_disease"):
            st.write(f"🛑 Detected Issue: **{st.session_state.detected_disease}**")
        
        crop = "Tomato" # Simplified for both
    with col_in2:
        requirement = st.text_input(f"{actor}: Search Query", value=initial_req)

    # Automatic trigger if redirected
    if initial_req and not st.session_state.get(f"searched_{actor}"):
        st.session_state[f"searched_{actor}"] = True
        run_search = True
    else:
        run_search = st.button(f"Search {actor}")

    col1, col2 = st.columns(2)
    with col1:
        if run_search:
            with st.spinner(f"Finding the best {actor.lower()}s for you..."):
                location = st.session_state.location or 'unknown location'
                disease_context = f" for treatment of {st.session_state.get('detected_disease')}" if st.session_state.get('detected_disease') else ""
                
                if actor == "Shop":
                    search_prompt = f"As an agricultural AI, find/recommend 5 fertilizer shops or online products for {requirement}{disease_context} near {location}. For each product/shop, provide the Fertilizer Name, Estimated Cost (₹), and a brief usage advice. Format as a clean, easy-to-read list."
                else:
                    search_prompt = f"As an agricultural AI, find/recommend 5 plant doctors or experts for {crop}{disease_context} with requirement: {requirement} near {location}. Provide name, contact detail (simulated), and specialized service. Format as a clean list."
                
                # Use GPT for high-accuracy shop/doctor searches
                response = call_openrouter([{"role": "user", "content": search_prompt}], model="openai/gpt-4o-mini")
                if "error" not in response.lower() or "401" not in response:
                    st.success(f"Found {actor}s!")
                    st.markdown(response)
                else:
                    st.error(f"Search failed: {response}")

    with col2:
        if st.button("Show all nearby"):
            with st.spinner(f"Listing all major {actor.lower()} options..."):
                search_prompt = f"List all major {actor.lower()} options for {crop} farming. Include pricing estimates and usage summary."
                response = call_openrouter([{"role": "user", "content": search_prompt}])
                st.markdown(response)


def contact_page():
    st.title("📞 Contact")
    st.markdown(
        """
        **AI Farm Agent Team**  
        Email: support@aifarmagent.local  
        Services: Vision, Climate, Soil, Water, Market, Execution  
        """
    )


def main():
    st.set_page_config(page_title="Agri Super Agent", layout="wide")
    ensure_session_defaults()
    apply_local_font(st.session_state.language)

    lang_text = TRANSLATIONS[st.session_state.language]
    
    # NAVIGATION AT ABSOLUTE TOP
    cols = st.columns(5)
    menu_items = [lang_text["home"], lang_text["chat"], lang_text["shops"], lang_text["doctors"], lang_text["contact"]]
    
    for i, item in enumerate(menu_items):
        if cols[i].button(item, use_container_width=True, type="primary" if st.session_state.menu_choice == item else "secondary"):
            st.session_state.menu_choice = item
            st.rerun()

    st.markdown('<div id="main-content">', unsafe_allow_html=True)
    sidebar_controls(lang_text)
    
    # Mode switch reset logic
    if "prev_mode" not in st.session_state:
        st.session_state.prev_mode = st.session_state.analysis_mode
    
    if st.session_state.analysis_mode != st.session_state.prev_mode:
        st.session_state.detection_result = None
        st.session_state.soil_analysis_result = None
        st.session_state.prev_mode = st.session_state.analysis_mode
        st.rerun()

    apply_local_font(st.session_state.language)

    menu = st.session_state.menu_choice

    if menu == lang_text["home"]:
        home_page(lang_text)
    elif menu == lang_text["chat"]:
        chat_page()
    elif menu == lang_text["shops"]:
        shop_or_doctors_page("🛒 Fertilizer Shop", "Shop", lang_text)
    elif menu == lang_text["doctors"]:
        shop_or_doctors_page("🩺 Doctors", "Doctors", lang_text)
    else:
        contact_page()
    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
