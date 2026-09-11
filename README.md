# EcoPay5G — AI-Driven Smart Recycling Kiosk

> **GSMA MENA Ignite Hackathon Prototype Simulation**  
> EcoPay5G is an interactive prototype simulation developed for the GSMA MENA Ignite Hackathon. It demonstrates how 5G CAMARA Network APIs, computer vision, and autonomous AI agents can be integrated into smart city infrastructure to automate waste processing, prevent fraud, and reward sustainable habits.

---

## Authors & Contributors

* **Rida Dandane** — [EcoPay5G](https://github.com/DandaneRida/EcoPay5G)
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

### 3. Flutter Mobile Application (`mobile_app`)
A mobile client interface designed for recycling kiosk interactions and secure identity verification.

---

## Directory Structure

```text
EcoPay5G/
├── mobile_app/                  # Flutter Mobile Application
│   ├── android/                 # Android native configuration
│   ├── ios/                     # iOS native configuration
│   ├── lib/
│   │   ├── core/                # Global constants & configuration
│   │   │   ├── constants.dart
│   │   │   └── constants.template.dart
│   │   ├── models/              # Data models
│   │   ├── screens/             # Application UI screens
│   │   │   ├── result_screen.dart
│   │   │   ├── scanner_screen.dart
│   │   │   └── verification_screen.dart
│   │   ├── services/            # Nokia CAMARA API integration
│   │   │   └── camara_service.dart
│   │   └── main.dart            # Flutter entry point
│   ├── pubspec.yaml             # Flutter dependencies
│   └── README.md
├── app/                         # Streamlit Kiosk UI & Backend Agent
│   ├── agent/                   # LangGraph state machine, nodes, and tools
│   │   ├── graph.py
│   │   ├── nodes.py
│   │   └── state.py
│   ├── camara/                  # Nokia Network-as-Code API gateway client
│   │   ├── client.py
│   │   ├── config.py
│   │   └── __init__.py
│   └── main.py                  # Streamlit web interface
├── models/                      # YOLOv8 weight files
│   ├── yolov8_best_smartdetection.pt
│   └── yolov8_best.pt
├── notebooks/                   # Jupyter training and experimentation notebooks
├── .env.example                 # Environment variables template
├── .gitignore
├── README.md
└── requirements.txt

```

---

## Mobile Application Workflow & Usage

The Flutter application (`mobile_app`) provides a secure user interface for interacting with the kiosk:

1. **Identity & SIM Security Verification (`verification_screen.dart`)**:
* The user inputs their mobile number in international E.164 format (e.g., `+358400000001`).
* The app communicates with Nokia CAMARA Network APIs through `camara_service.dart` to verify that the phone number matches the active network session and check for recent SIM swap fraud attempts.
* Access to the kiosk scanner is denied if network security checks fail.


2. **QR Code Scanning (`scanner_screen.dart`)**:
* Once identity is verified, the camera scanner activates to scan the session QR code generated on the EcoPay5G recycling kiosk display.


3. **Transaction Result & Rewards (`result_screen.dart`)**:
* Displays real-time confirmation of the deposit, total recyclables processed, and eco-credits credited to the subscriber's account.



### Running the Mobile App

```bash
cd mobile_app
flutter pub get
flutter run

```

*Note: For Windows builds, if your project is on a different drive than your Flutter Pub Cache (e.g., `D:` vs `C:`), ensure `kotlin.incremental=false` is set in `android/gradle.properties`.*

---

## Installation & Local Setup (Kiosk & Web Backend)

### Prerequisites

* Python 3.10 or higher
* Flutter SDK (for mobile app)
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
NOKIA_NV_URL=[https://network-as-code.p-eu.rapidapi.com/passthrough/camara/v1/number-verification/number-verification/v0/verify](https://network-as-code.p-eu.rapidapi.com/passthrough/camara/v1/number-verification/number-verification/v0/verify)
NOKIA_SIM_SWAP_URL=[https://network-as-code.p-eu.rapidapi.com/passthrough/camara/v1/sim-swap/sim-swap/v0/check](https://network-as-code.p-eu.rapidapi.com/passthrough/camara/v1/sim-swap/sim-swap/v0/check)
NOKIA_QOD_URL=NOKIA_QUALITY_ON_DEMAND_URL

# LLM Agent Gateway
GROQ_API_KEY=your_groq_api_key

# Remote Vision API Identifier (Hugging Face Space)
COLAB_VISION_URL=RidaDandane/ecopay5g-vision-api

```

---

## Running the Kiosk Simulation

### Option A: Local Execution (Default)

To run the full Streamlit application with embedded local YOLOv8 inference:

```bash
streamlit run app/main.py

```

### Option B: Remote Acceleration via Hugging Face ZeroGPU Space

If local hardware limits prevent local YOLO execution, vision inference is automatically routed to the Hugging Face ZeroGPU Space:

1. Ensure `COLAB_VISION_URL` is configured in `.env`.
2. Launch the Streamlit kiosk interface:

```bash
streamlit run app/main.py

```

Access the web interface at `http://localhost:8501`.

---

## Hackathon Context & Acknowledgments

This software is submitted as a prototype demonstration for the **GSMA MENA Ignite Hackathon 2026**. Special thanks to GSMA, Nokia Network-as-Code, and RapidAPI for providing network gateway access, technical support, and mentorship.