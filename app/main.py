import os
import sys
import tempfile
import subprocess
import json
import qrcode
import io

# Runtime patch for headless cloud environments (e.g., Streamlit Cloud)
# Programmatically uninstalls 'opencv-python' to force reliance on 'opencv-python-headless',
# preventing missing libGL.so.1 shared library initialization errors.
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
from PIL import Image, ImageDraw, ImageFont
from langchain_core.messages import HumanMessage

# Resolve and inject project root directory into system path for cross-environment imports
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.camara.config import COLAB_VISION_URL
from app.agent.graph import app_agent

# Configure Streamlit page parameters
st.set_page_config(
    page_title="EcoPay 5G - Smart Bin Kiosk",
    layout="wide",
    initial_sidebar_state="expanded"
)

def draw_bounding_box(image: Image.Image, box_coords: list, label: str, confidence: float) -> Image.Image:
    """
    Draws a bounding box rectangle and class label overlay onto a PIL Image copy.
    Converts image to RGB mode first to prevent palette/256-color limit errors.
    """
    # Convert image to RGB mode to handle PNG/GIF palette-indexed images
    annotated = image.convert("RGB")
    draw = ImageDraw.Draw(annotated)
    
    xmin, ymin, xmax, ymax = box_coords
    
    # Bounding box color configuration (Bright Green)
    outline_color = "#00FF00"
    line_width = 4
    
    # Draw bounding box rectangle
    draw.rectangle([xmin, ymin, xmax, ymax], outline=outline_color, width=line_width)
    
    # Render label text
    text = f"{label.upper()} {confidence * 100:.1f}%"
    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    # Draw label box overlay
    text_pos = (xmin + 5, max(0, ymin - 15))
    draw.text(text_pos, text, fill=outline_color, font=font)
    
    return annotated

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

    # Verify model weight files exist on local disk
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
    Executes the computer vision processing pipeline.
    
    Strategy 1: Attempts local inference using YOLOv8 models.
    Strategy 2: Remote fallback querying Hugging Face ZeroGPU Space via gradio_client.
    
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
                "confidence": 0.0,
                "box_coords": None
            }

        # Extract bounding box coordinates
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
                "box_coords": box_coords,
                "cropped_image": cropped_image
            }

        return {
            "status": "CLASSIFICATION_FAILED",
            "is_waste": True,
            "detected_class": "UNKNOWN",
            "confidence": 0.0,
            "box_coords": box_coords
        }

    # Strategy 2: Remote Hugging Face Space Inference Fallback
    space_target = str(COLAB_VISION_URL).strip() if COLAB_VISION_URL else ""
    if not space_target:
        raise ValueError(
            "Local YOLO models could not be loaded, and COLAB_VISION_URL is not configured "
            "in Streamlit secrets or environment variables."
        )

    # Persist input file buffer to a temporary file for gradio_client file handling
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
        tmp_file.write(img_file.getvalue())
        tmp_path = tmp_file.name

    try:
        from gradio_client import Client, handle_file
        client = Client(space_target)
        result = client.predict(
            image=handle_file(tmp_path),
            api_name="/predict"
        )
        return result
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


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
        st.image(Image.open(img_file), caption="Captured Waste Frame", use_container_width=True)

with col2:
    st.subheader("2. Telemetry Input")

    # Removed the phone number input field to ensure kiosk anonymity
    # Users will claim their deposit using the generated QR code instead

    weight_unit = st.selectbox("Select Weight Unit", options=["g", "kg"])
    if weight_unit == "g":
        measured_weight = st.number_input("Scale Measurement", min_value=1, max_value=999, value=150, step=1)
        weight_in_grams = int(measured_weight)
    else:
        measured_weight = st.number_input("Scale Measurement", min_value=1.0, max_value=10.0, value=1.0, step=0.1)
        weight_in_grams = int(measured_weight * 1000)

    btn_submit = st.button("Submit Deposit", type="primary", use_container_width=True)

if img_file and btn_submit:
    st.markdown("---")
    st.subheader("3. AI Agent Execution & CAMARA Logic")

    with st.spinner("Executing Computer Vision Pipeline..."):
        try:
            data = process_vision_inference(img_file)

            if data.get("status") == "SUCCESS" and data.get("is_waste"):
                detected_class = data.get("detected_class", "unknown").upper()
                confidence = data.get("confidence", 0.0)
                box_coords = data.get("box_coords")

                st.success(f"Object Classified: {detected_class} (Confidence: {confidence * 100:.1f}%)")

                # Render annotated image with bounding box
                if box_coords:
                    original_img = Image.open(img_file)
                    annotated_img = draw_bounding_box(original_img, box_coords, detected_class, confidence)
                    st.image(annotated_img, caption="Detected Waste Bounding Box Overlay", use_container_width=True)
                elif "cropped_image" in data:
                    st.image(data["cropped_image"], caption="Cropped Object Region", width=200)

                # Use a hardcoded generic kiosk identifier to satisfy backend tool schemas
                # without requiring the user to manually type a number on the public interface
                kiosk_phone = "+358400000001"
                user_prompt = f"Process deposit: Phone={kiosk_phone}, Waste={detected_class}, Weight={weight_in_grams}g"

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
                                    
                # ---------------------------------------------------------
                # Step 4: Deposit Validation & QR Code Generation
                # ---------------------------------------------------------
                st.markdown("---")
                st.subheader("4. Deposit Validation (Scan QR)")
                
                # Evaluation rates for calculating points based on material type
                point_rates = {
                    "PLASTIC": 0.10,
                    "GLASS": 0.05,
                    "PAPER": 0.08,
                    "METAL": 0.15,
                    "CARDBOARD": 0.07
                }
                
                # Calculate final point allocation
                rate = point_rates.get(detected_class, 0.05)
                calculated_points = round(weight_in_grams * rate, 2)
                
                # Construct JSON payload for the Flutter mobile application
                # Notice that user identity/phone is omitted for security
                qr_payload = {
                    "waste_class": detected_class,
                    "weight_g": weight_in_grams,
                    "points": calculated_points
                }
                
                # Generate in-memory PNG representation of the QR code
                qr_img = qrcode.make(json.dumps(qr_payload))
                buf = io.BytesIO()
                qr_img.save(buf, format="PNG")
                
                # Render the final QR code to the user interface
                st.image(buf.getvalue(), caption="Scan with the EcoPay App to claim your points", width=250)

            else:
                st.error("No valid recyclable waste detected in the frame.")

        except Exception as e:
            st.error(f"Execution failed: {str(e)}")