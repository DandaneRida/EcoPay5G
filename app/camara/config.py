import os
from dotenv import load_dotenv

load_dotenv()

NOKIA_NAC_API_KEY = os.getenv("NOKIA_NAC_API_KEY", "")
NOKIA_NV_URL = os.getenv("NOKIA_NV_URL", "")
NOKIA_SIM_SWAP_URL = os.getenv("NOKIA_SIM_SWAP_URL", "")
NOKIA_QOD_URL = os.getenv("NOKIA_QOD_URL", "")

COLAB_VISION_URL = os.getenv("COLAB_VISION_URL", "http://127.0.0.1:8000/predict")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")