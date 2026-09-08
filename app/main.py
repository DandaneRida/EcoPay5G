import os
import sys
import subprocess

# Runtime environment patch for headless cloud deployments (e.g., Streamlit Cloud)
# Programmatically uninstalls 'opencv-python' to prevent libGL.so.1 missing shared object errors
# and forces Ultralytics/OpenCV to rely exclusively on 'opencv-python-headless'.
try:
    subprocess.run(
        [sys.executable, "-m", "pip", "uninstall", "-y", "opencv-python"],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )
except Exception:
    pass

import requests
import streamlit as st
from PIL import Image
from langchain_core.messages import HumanMessage

# Resolve and set root directory paths across execution environments
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

# Ensure project root is available in sys.path for local module imports
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.camara.config import COLAB_VISION_URL
from app.agent.graph import app_agent

# Configure Streamlit application interface
st.set_page_config(
    page_title="EcoPay 5G - Smart Bin Kiosk",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_resource
def load_local_vision_models():
    """
    Loads two-stage YOLOv8 models into memory with resource caching.
    
    Stage 1: Object Detection model (yolov8_best_smartdetection.pt)
    Stage 2: Material Classification model (yolov8_best.pt)
    
    Returns:
        tuple: (model_detect, model_classify) if successfully loaded, otherwise (None, None).
    """
    detect_path = os.path.join(PROJECT_ROOT, "models", "yolov8_best_smartdetection.pt")
    classify_path = os.path.join(PROJECT_ROOT, "models", "yolov8_best.pt")

    # Check if local model weight files exist on disk
    if not (os.path.exists(detect_path) and os.path.exists(classify_path)):
        return None, None

    try:
        from ultralytics import YOLO
        model_detect = YOLO(detect_path)
        model_classify = YOLO(classify_path)
        return model_detect, model_classify
    except Exception as err:
        st.warning(f"Failed to initialize local YOLO models: {str(err)}")
        return None, None


def process_vision_inference(img_file):
    """
    Executes the computer vision pipeline.
    
    Attempts local inference using YOLOv8 models first. If local models 
    are unavailable, it falls back to a remote API endpoint defined by COLAB_VISION_URL.
    
    Args:
        img_file: Streamlit UploadedFile object containing the deposit image.
        
    Returns:
        dict: Standardized inference result payload.
    """
    model_detect, model_classify = load_local_vision_models()

    # Strategy 1: Local YOLOv8 Inference Pipeline
    if model_detect is not None and model_classify is not None:
        image = Image.open(img_file)

        # Stage 1: Object Detection
        res_detect = model_detect(image)
        if len(res_detect[0].boxes) == 0:
            return {
                "status": "SUCCESS",
                "is_waste": False,
                "detected_class": None,
                "confidence": 0.0
            }

        # Crop detected object bounding box
        box_coords = res_detect[0].boxes[0].xyxy[0].tolist()
        cropped_image = image.crop((box_coords[0], box_coords[1], box_coords[2], box_coords[3]))

        # Stage 2: Material Classification
        res_classify = model_classify(cropped_image)
        if len(res_classify[0].boxes) > 0:
            box_cls = res_classify[0].boxes[0]
            detected_class = model_classify.names[int(box_cls.cls)]
            confidence = float(box_cls.conf)
            return {
                "status": "SUCCESS",
                "is_waste": True,
                "detected_class": detected_class,
                "confidence": confidence,
                "cropped_image": cropped_image
            }

        return {
            "status": "CLASSIFICATION_FAILED",
            "is_waste": True,
            "detected_class": "UNKNOWN",
            "confidence": 0.0
        }

    # Strategy 2: Remote API Fallback
    if not COLAB_VISION_URL or not str(COLAB_VISION_URL).strip().startswith(("http://", "https://")):
        raise ValueError(
            "Local YOLO models could not be loaded from the 'models/' directory, "
            "and COLAB_VISION_URL is not configured with a valid HTTP/HTTPS endpoint in secrets or environment variables."
        )

    files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
    response = requests.post(COLAB_VISION_URL, files=files, timeout=20)
    
    if response.status_code == 200:
        return response.json()
    else:
        raise RuntimeError(
            f"Remote Vision API returned HTTP error code {response.status_code}: {response.text}"
        )


# ---------------------------------------------------------
# User Interface Definition
# ---------------------------------------------------------
st.title("EcoPay 5G - Smart Bin Kiosk System")
st.markdown("---")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. Optical Sensing")
    img_file = st.file_uploader(
        "Upload deposit image",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=False
    )
    if img_file:
        st.image(Image.open(img_file), caption="Captured Waste Frame", width="stretch")

with col2:
    st.subheader("2. Telemetry Input")

    user_phone = st.text_input(
        "Enter Subscriber Phone Number",
        value="+358400000001",
        help="Format: International E.164 format (e.g., +358400000001)"
    )

    weight_unit = st.selectbox("Select Weight Unit", options=["g", "kg"])
    if weight_unit == "g":
        measured_weight = st.number_input("Scale Measurement", min_value=1, max_value=999, value=150, step=1)
        weight_in_grams = int(measured_weight)
    else:
        measured_weight = st.number_input("Scale Measurement", min_value=1.0, max_value=10.0, value=1.0, step=0.1)
        weight_in_grams = int(measured_weight * 1000)

    btn_submit = st.button("Submit Deposit", type="primary", width="stretch")

if img_file and btn_submit:
    st.markdown("---")
    st.subheader("3. AI Agent Execution & CAMARA Logic")

    with st.spinner("Executing Computer Vision Pipeline..."):
        try:
            data = process_vision_inference(img_file)

            if data.get("status") == "SUCCESS" and data.get("is_waste"):
                detected_class = data.get("detected_class", "unknown")
                confidence = data.get("confidence", 0.0)
                st.success(f"Object Classified: {detected_class.upper()} (Confidence: {confidence * 100:.1f}%)")

                if "cropped_image" in data:
                    st.image(data["cropped_image"], caption="Cropped Object Region", width=200)

                user_prompt = f"Process deposit: Phone={user_phone}, Waste={detected_class}, Weight={weight_in_grams}g"

                with st.spinner("Executing security verification and network logic..."):
                    inputs = {"messages": [HumanMessage(content=user_prompt)]}
                    events = app_agent.stream(inputs)

                    for event in events:
                        for node_name, value in event.items():
                            with st.expander(f"Execution Step: {node_name.upper()}", expanded=True):
                                msg = value["messages"][-1]
                                if hasattr(msg, "tool_calls") and msg.tool_calls:
                                    for tc in msg.tool_calls:
                                        st.info(f"[SYSTEM] Invoking Tool: {tc['name']} | Parameters: {tc['args']}")
                                if msg.content:
                                    st.markdown(msg.content)
            else:
                st.error("No valid recyclable waste detected in the frame.")

        except Exception as e:
            st.error(f"Execution failed: {str(e)}")