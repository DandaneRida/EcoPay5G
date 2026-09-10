# EcoPay5G — AI-Driven Smart Recycling Kiosk

> **GSMA MENA Ignite Hackathon Prototype Simulation**  
> EcoPay5G is an interactive prototype simulation developed for the GSMA MENA Ignite Hackathon[cite: 4]. It demonstrates how 5G CAMARA Network APIs, computer vision, and autonomous AI agents can be integrated into smart city infrastructure to automate waste processing, prevent fraud, and reward sustainable habits.

---

## Authors & Contributors

* **Rida Dandane** — [EcoPay5G](https://github.com/DandaneRida)
* **Youssef Es-Saaidi** — [YOLOv8 Waste Detection Model Repository](https://github.com/YoussefAIDT/waste-detection-yolov8)

---

## Overview

EcoPay5G automates the waste recycling workflow at automated kiosk stations. Using a two-stage YOLOv8 vision pipeline combined with an autonomous LangGraph agent, the platform identifies deposited recyclables, verifies subscriber identity over cellular networks, mitigates account takeover risks, and dynamically requests 5G quality-of-service boosts for heavy data telemetry.

The prototype supports dual execution modes: running vision inference directly on the host machine using embedded model weights or offloading computation asynchronously to a remote **Hugging Face ZeroGPU Space** via `gradio_client`.

---

## System Architecture & Key Components

### 1. Two-Stage Vision Pipeline
- **Object Detection**: Utilizes `yolov8_best_smartdetection.pt` to detect the presence of deposited objects and extract bounding box coordinates.
- **Bounding Box Cropping**: Dynamically crops the isolated item from the captured camera frame.
- **Material Classification**: Evaluates the cropped region using `yolov8_best.pt` to classify material composition (e.g., Plastic, Glass, Metal).

### 2. Autonomous LangGraph Agent
An event-driven LangGraph agent coordinates business logic and network tools:
- **Number Verification (3-legged CAMARA API)**: Confirms mobile subscriber identity via cellular network gateway authentication.
- **SIM Swap Detection (2-legged CAMARA API)**: Checks for recent SIM modifications within a 24-hour window to block fraudulent reward transactions.
- **Quality on Demand (QoD) (2-legged CAMARA API)**: Requests temporary 5G network priority for transactions involving large weight volumes or complex telemetry data.

---

## Directory Structure

```text
EcoPay5G/
├── app/
│   ├── agent/             # LangGraph state machine, nodes, and tool wrappers
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── camara/            # Nokia Network-as-Code API gateway client
│   │   ├── client.py
│   │   ├── config.py
│   │   └── __init__.py
│   └── main.py            # Streamlit main application and user interface
├── models/                # YOLOv8 weight files
│   ├── yolov8_best_smartdetection.pt
│   └── yolov8_best.pt
├── .env.example           # Environment variables template
├── .gitignore
├── README.md
└── requirements.txt

```

---

## Installation & Local Setup

### Prerequisites

* Python 3.10 or higher
* Git

### 1. Repository Setup

```bash
git clone [https://github.com/DandaneRida/EcoPay5G.git](https://github.com/DandaneRida/EcoPay5G.git)
cd EcoPay5G

```

### 2. Virtual Environment Configuration

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

```

### 3. Environment Variables Setup

Create a `.env` file in the project root based on `.env.example`:

```env
# Nokia Network-as-Code Gateway Settings
NOKIA_NAC_API_KEY=your_nokia_rapidapi_key
NOKIA_NV_URL=NOKIA_NUMBER_VERIFICATION_URL
NOKIA_SIM_SWAP_URL=NOKIA_SIM_SWAP_URL
NOKIA_QOD_URL=NOKIA_QUALITY_ON_DEMAND_URL

# LLM Agent Gateway
GROQ_API_KEY=your_groq_api_key

# Remote Vision API Identifier (Hugging Face Space)
COLAB_VISION_URL=RidaDandane/ecopay5g-vision-api

```

*Note: When `NOKIA_NAC_API_KEY` is omitted, the network client automatically falls back to local CAMARA mock handlers for offline testing.*

---

## Running the Prototype Simulation

### Option A: Local Execution (Default)

To run the full application with embedded local YOLOv8 inference:

```bash
streamlit run app/main.py

```

### Option B: Remote Acceleration via Hugging Face ZeroGPU Space

If local hardware resources or shared cloud container limits (such as Streamlit Cloud) prevent local YOLO execution, vision inference is automatically routed to the Hugging Face ZeroGPU Space:

1. Ensure the vision backend is active on Hugging Face Spaces .
2. Set the `COLAB_VISION_URL` variable in `.env` or Streamlit Cloud Secrets:
```toml
COLAB_VISION_URL = "YOUR_VISION_URL" or use COLAB_VISION_URL="RidaDandane/ecopay5g-vision-api"

```


3. Start the main Streamlit application:
```bash
streamlit run app/main.py

```



Access the interface in your web browser at `http://localhost:8501`.

---

## Hackathon Context & Acknowledgments

This software is submitted as a prototype demonstration for the **GSMA MENA Ignite Hackathon 2026**. Special thanks to GSMA, Nokia Network-as-Code, and RapidAPI for providing network gateway access, technical support, and mentorship.

