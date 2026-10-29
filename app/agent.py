# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.firestore_tools import (
    add_destination_note,
    get_destination,
    save_travel_itinerary,
    search_destinations,
)
from app.image_tools import generate_destination_image
from app.maps_tools import geocode_address, search_nearby_places
from app.rag_tools import consult_herbal_knowledge
from app.video_tools import generate_destination_video

AGENT_ENGINE_RESOURCE_NAME = (
    "projects/813594678577/locations/us-east1/reasoningEngines/2450019769940705280"
)
SANDBOX_RESOURCE_NAME = (
    "projects/813594678577/locations/us-east1/reasoningEngines/2450019769940705280/sandboxEnvironments/2382773638785925120"
)

code_executor = AgentEngineSandboxCodeExecutor(
    sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    agent_engine_resource_name=AGENT_ENGINE_RESOURCE_NAME,
)


async def generate_memories_callback(callback_context: CallbackContext):
    """Callback to extract durable memories and preferences after each turn."""
    await callback_context.add_session_to_memory()
    return None


def get_weather(query: str) -> str:
    """Simulates a web search. Use it get information on weather.

    Args:
        query: A string containing the location to get weather information for.

    Returns:
        A string with the simulated weather information for the queried location.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        return "It's 60 degrees and foggy."
    return "It's 90 degrees and sunny."


def get_current_time(query: str) -> str:
    """Simulates getting the current time for a city.

    Args:
        city: The name of the city to get the current time for.

    Returns:
        A string with the current time information.
    """
    if "sf" in query.lower() or "san francisco" in query.lower():
        tz_identifier = "America/Los_Angeles"
    else:
        return f"Sorry, I don't have timezone information for query: {query}."

    tz = ZoneInfo(tz_identifier)
    now = datetime.datetime.now(tz)
    return f"The current time for query {query} is {now.strftime('%Y-%m-%d %H:%M:%S %Z%z')}"


import json
import urllib.request


def get_live_exchange_rates(base_currency: str = "USD") -> str:
    """Fetches live real-time currency exchange rates from the free ExchangeRate public API.

    Args:
        base_currency: 3-letter currency code for the base currency (default 'USD').

    Returns:
        A formatted JSON string with live exchange rates for major travel currencies.
    """
    base = base_currency.upper().strip()
    url = f"https://open.er-api.com/v6/latest/{base}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            if data.get("result") == "success":
                rates = data.get("rates", {})
                major = ["USD", "EUR", "JPY", "GBP", "CAD", "AUD", "CHF", "CNY", "INR", "SGD", "MXN"]
                filtered = {c: rates[c] for c in major if c in rates}
                return json.dumps(
                    {
                        "status": "success",
                        "base_currency": base,
                        "last_updated_utc": data.get("time_last_update_utc"),
                        "rates": filtered,
                    },
                    indent=2,
                )
            return f"API returned error: {data.get('error-type', 'Unknown error')}"
    except Exception as e:
        return f"Failed to fetch live exchange rates: {str(e)}"


def convert_currency(amount: float, from_currency: str, to_currency: str) -> str:
    """Converts a monetary amount or budget between currencies using live or fallback exchange rates.

    Args:
        amount: The monetary value or budget amount to convert.
        from_currency: 3-letter source currency code (e.g. 'USD', 'JPY', 'EUR', 'GBP', 'CAD', 'AUD').
        to_currency: 3-letter target currency code (e.g. 'USD', 'JPY', 'EUR', 'GBP', 'CAD', 'AUD').

    Returns:
        Formatted string containing the converted amount and current rate.
    """
    src = from_currency.upper().strip()
    dst = to_currency.upper().strip()

    # Try live rate first
    try:
        url = f"https://open.er-api.com/v6/latest/{src}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get("result") == "success" and dst in data.get("rates", {}):
                rate = data["rates"][dst]
                converted = amount * rate
                return f"{amount:.2f} {src} = {converted:.2f} {dst} (Live Rate: 1 {src} = {rate:.4f} {dst})"
    except Exception:
        pass

    # Fallback to static rates
    rates = {
        "USD": 1.0,
        "JPY": 155.0,
        "EUR": 0.92,
        "GBP": 0.79,
        "CAD": 1.36,
        "AUD": 1.51,
    }

    if src not in rates or dst not in rates:
        return f"Unsupported currency code. Supported currencies: {', '.join(rates.keys())}"

    amount_in_usd = amount / rates[src]
    converted = amount_in_usd * rates[dst]
    rate = rates[dst] / rates[src]

    return f"{amount:.2f} {src} = {converted:.2f} {dst} (Fallback Rate: 1 {src} = {rate:.4f} {dst})"


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

a2ui_instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are a helpful AI travel concierge designed to provide accurate travel, weather, wellness, timezone, and destination information.\n\n"
        "CRITICAL ALLERGY & SAFETY DIRECTIVE:\n"
        "- Actively track and remember all user allergies (e.g. food allergies, dietary restrictions, environmental/medical allergies) and travel preferences stated across conversations.\n"
        "- Whenever the user mentions an allergy, acknowledge it clearly and record it.\n"
        "- Before suggesting restaurants, food, activities, or travel plans, check preloaded memories to ensure NO recommended item contains or triggers any user allergy.\n\n"
        "FIRESTORE DESTINATION & ITINERARY BACKEND:\n"
        "- Use search_destinations and get_destination tools to query destination information, budget guidelines, and top attractions stored in Firestore.\n"
        "- Use save_travel_itinerary and add_destination_note tools to save created itineraries or tips into Firestore for the user.\n\n"
        "LIVE CURRENCY & BUDGET CONVERSION:\n"
        "- Use get_live_exchange_rates and convert_currency to query live real-time exchange rates and convert travel budgets/expenses for international travel.\n\n"
        "GEOCODING & PLACES SEARCH (GOOGLE MAPS):\n"
        "- Use geocode_address to convert addresses or landmark names into latitude/longitude coordinates.\n"
        "- Use search_nearby_places to discover nearby restaurants, cafes, tourist attractions, or lodging around specific coordinates.\n\n"
        "HERBAL & WELLNESS KNOWLEDGE (CULPEPER'S COMPLETE HERBAL RAG):\n"
        "- Use consult_herbal_knowledge to search Culpeper's Herbal corpus when answering questions about plants, herbal tea remedies, natural travel wellness, or traditional remedies.\n\n"
        "DESTINATION IMAGE & VIDEO GENERATION:\n"
        "- Use generate_destination_image to generate AI destination photos or landscape previews when requested.\n"
        "- Use generate_destination_video to generate AI short destination preview videos using Google Omni model (gemini-omni-flash-preview) when requested by the user.\n\n"
        "SANDBOX CODE EXECUTION:\n"
        "- You have a secure Python code sandbox environment enabled via AgentEngineSandboxCodeExecutor. Use code execution blocks for complex math calculations, budget splits, or data analysis when helpful."
    ),
    workflow_description="Analyze the request, use tools when needed, and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)

root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    code_executor=code_executor,
    instruction=a2ui_instruction,
    tools=[
        PreloadMemoryTool(),
        get_weather,
        get_current_time,
        get_destination,
        search_destinations,
        save_travel_itinerary,
        add_destination_note,
        get_live_exchange_rates,
        convert_currency,
        geocode_address,
        search_nearby_places,
        consult_herbal_knowledge,
        generate_destination_image,
        generate_destination_video,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)

