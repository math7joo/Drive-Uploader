import streamlit as st
import os
import io
from PIL import Image
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from streamlit_paste_button import paste_image_button

# ── Config ───────────────────────────────────────────────────────────────────
SCOPES = ["https://www.googleapis.com/auth/drive.file"]
TOKEN_FILE = "token.json"
CREDS_FILE = "credentials.json"
FOLDER_ID = "1MFsIJJolZx9Aaxurxypcb-ZuVYn9vCMf"

# ── Modern UI & Custom CSS ──────────────────────────────────────────────────
st.set_page_config(page_title="CloudDrop | Image Uploader", page_icon="☁️", layout="centered")

st.markdown("""
<style>
    /* Main App Background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Title Styling */
    .main-title {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        color: #1e3a8a;
        text-align: center;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .sub-title {
        text-align: center;
        color: #4b5563;
        font-size: 1.1rem;
        margin-bottom: 30px;
    }

    /* Container Styling */
    .upload-container {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }

    /* Button Styling */
    .stButton > button {
        width: 100%;
        background: linear-gradient(90deg, #2563eb 0%, #1e40af 100%) !important;
        color: white !important;
        border-radius: 12px !important;
        border: none !important;
        padding: 12px 0px !important;
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4);
    }

    /* Success Link Box */
    .link-box {
        background-color: #f0fdf4;
        border: 2px dashed #22c55e;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-top: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ── Google Drive Auth ────────────────────────────────────────────────────────
@st.cache_resource
def get_drive_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_FILE):
                st.error("Missing credentials.json file!")
                st.stop()
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def upload_and_share(service, file_bytes, filename, mime_type):
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
    file_metadata = {"name": filename, "parents": [FOLDER_ID]}
    uploaded_file = service.files().create(body=file_metadata, media_body=media, fields="id,webViewLink").execute()
    service.permissions().create(fileId=uploaded_file["id"], body={"type": "anyone", "role": "reader"}).execute()
    final_file = service.files().get(fileId=uploaded_file["id"], fields="webViewLink").execute()
    return final_file["webViewLink"]

# ── Main UI ──────────────────────────────────────────────────────────────────
st.markdown('<h1 class="main-title">CloudDrop ☁️</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Instant Image Upload to Google Drive</p>', unsafe_allow_html=True)

# Main Section
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📁 Upload File")
        uploaded_file = st.file_uploader("Drop an image here", type=["png", "jpg", "jpeg", "webp"])

    with col2:
        st.markdown("### 📋 Quick Paste")
        pasted_image = paste_image_button("Click to Paste Image")

# Process Image
final_image_bytes = None
default_name = "image_upload.png"
mime_type = "image/png"

if uploaded_file:
    final_image_bytes = uploaded_file.read()
    default_name = uploaded_file.name
    mime_type = uploaded_file.type
    st.image(Image.open(io.BytesIO(final_image_bytes)), caption="Ready to upload", use_container_width=True)

elif pasted_image and pasted_image.image_data is not None:
    img_buffer = io.BytesIO()
    pasted_image.image_data.save(img_buffer, format="PNG")
    final_image_bytes = img_buffer.getvalue()
    st.image(pasted_image.image_data, caption="Clipboard Image Detected", use_container_width=True)

# Upload Section
if final_image_bytes:
    st.markdown("---")
    custom_name = st.text_input("🏷️ Image Name (Optional)", placeholder="e.g. math_homework_solution")
    
    if st.button("🚀 UPLOAD TO DRIVE"):
        with st.spinner("Uploading to Cloud..."):
            try:
                service = get_drive_service()
                
                # Naming Logic
                if custom_name.strip():
                    save_name = f"{custom_name.strip()}.png"
                else:
                    save_name = default_name
                
                link = upload_and_share(service, final_image_bytes, save_name, mime_type)
                
                st.markdown(f'''
                <div class="link-box">
                    <h3 style="color: #166534; margin-top:0;">✅ Upload Successful!</h3>
                    <p style="color: #374151;"><b>Name:</b> {save_name}</p>
                    <p style="color: #374151;">Shareable Link:</p>
                </div>
                ''', unsafe_allow_html=True)
                st.code(link, language=None)
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")
