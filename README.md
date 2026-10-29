# ✈️ Smart Travel Concierge

An intelligent, multi-tool AI travel assistant built with the **Google Agent Development Kit (ADK)** and deployed on **Google Agent Engine**. It offers personalized trip planning, live destination recommendations, real-time currency conversion, weather forecasts, herbal wellness tips, and AI-generated destination photos and video previews—all wrapped in a rich **A2UI** interactive interface.

![Smart Travel Concierge Demo](demo.gif)

---

## 🌟 Key Capabilities & Architecture

Based on the implemented codebase in `app/`, the agent integrates the following Google Cloud services and AI tools:

### 🧠 Long-Term Memory & Context
- **Vertex AI Memory Bank**: Preserves user travel preferences and past context across sessions using `PreloadMemoryTool` and automatic memory generation callbacks (`generate_memories_callback`).

### 🗄️ Database & Storage
- **Google Cloud Firestore**: Persists travel itineraries, destination metadata, and user notes via `get_destination`, `search_destinations`, `save_travel_itinerary`, and `add_destination_note`.
- **Google Cloud Storage**: Stores generated media assets in a public bucket (`smart-travel-concierge-media-*`) to produce public HTTPS URLs for A2UI rendering.

### 📚 Grounded Knowledge (RAG Engine)
- **Vertex AI RAG Engine**: Grounded on Culpeper's Complete Herbal corpus via `consult_herbal_knowledge` to provide traditional herbal remedies and travel wellness advice.

### 🎨 Multimodal Media Generation
- **Gemini AI Image Generation**: Generates high-quality destination photos using `generate_destination_image` (`imagen-3.0-generate-002`), saving artifacts to the playground and uploading to Cloud Storage.
- **Google Omni Video Generation**: Generates short travel preview videos using `gemini-omni-flash-preview` in the `global` region via `generate_destination_video`.

### 📍 Maps, Weather & Travel Utilities
- **Google Maps & Places API**: Converts locations to coordinates with `geocode_address` and discovers attractions/dining with `search_nearby_places`.
- **Live Travel Tools**: Fetches live exchange rates (`get_live_exchange_rates`), performs currency conversion (`convert_currency`), retrieves weather (`get_weather`), and checks current time (`get_current_time`).
- **Python Code Sandbox**: Executes complex budget splitting and financial calculations inside a secure `AgentEngineSandboxCodeExecutor` environment.

### 📱 Rich Display & Frontend UI
- **A2UI Rendering**: Formats model output into native UI components (`Card`, `Column`, `Row`, `Text`, `Image`) using an `after_model_callback`.
- **Custom Chat Web Frontend**: FastAPI proxy serving a modern web interface with Dark Mode, New Session reset, Typing Indicator, Lightbox modal image viewer, and dynamic follow-up chips.

---

## 🚧 Planned / Future Roadmap
*(Features from initial concept not yet implemented in current code)*
- **Live Flight & Hotel Booking Transactions**: Direct API integration with GDS / hotel reservation platforms.
- **Multi-User Collaborative Itineraries**: Real-time multi-user editing of travel plans.

---

## 🚀 Local Setup & Installation

### Prerequisites
- Python 3.10+
- Google Cloud SDK (`gcloud`) with access to Vertex AI, Firestore, and Cloud Storage.

### 1. Clone & Set Up Python Environment
```bash
cd smart-travel-concierge
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
Set the required Google Cloud variables:
```bash
export GOOGLE_CLOUD_PROJECT="<your-gcp-project-id>"
export GOOGLE_CLOUD_LOCATION="us-east1"
export GOOGLE_MAPS_API_KEY="<your-google-maps-api-key>"
export AGENT_DIRECTORY="app"
```

If connecting your local frontend to a deployed Agent Engine resource:
```bash
export AGENT_ENGINE_RESOURCE_NAME="projects/<project-number>/locations/us-east1/reasoningEngines/<engine-id>"
```

### 3. Run the Agent Locally (ADK Web Developer UI)
To test the agent using the ADK development web interface:
```bash
adk web app
```

### 4. Run the Web Frontend Locally
To launch the custom FastAPI chat web proxy and frontend:
```bash
cd frontend
pip install -r requirements.txt
python main.py
```
Open your browser to the local server port indicated by the startup logs (typically port `8080`).

---

## 🚢 Deployment

### Deploy Agent to Vertex AI Agent Runtime
```bash
agents-cli deploy --project <your-gcp-project-id> --region us-east1
```

### Deploy Frontend to Cloud Run
```bash
cd frontend
gcloud run deploy smart-travel-concierge-frontend \
  --source . \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="<your-agent-engine-resource-name>",AGENT_DIRECTORY="app"
```
