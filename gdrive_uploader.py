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

# ── Page & Style ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="ارفع صورة", page_icon="☁️", layout="centered")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; direction: rtl; }
.stApp { background: #f5f7ff; }
.title { text-align: center; font-size: 2rem; font-weight: 900; color: #2d3a8c; margin-bottom: 0.2rem; }
.subtitle { text-align: center; color: #888; font-size: 0.9rem; margin-bottom: 2rem; }
.link-box { background: #eaffef; border: 2px solid #34c759; border-radius: 12px; padding: 1rem 1.5rem; margin-top: 1rem; text-align: center; }
.link-label { color: #1a7a3a; font-weight: 700; font-size: 1rem; margin-bottom: 0.5rem; }
.stButton > button { background: #2d3a8c !important; color: white !important; font-family: 'Cairo', sans-serif !important; font-weight: 700 !important; font-size: 1.1rem !important; border-radius: 10px !important; border: none !important; width: 100%; padding: 0.7rem !important; }
.stButton > button:hover { background: #1a2560 !important; }
/* تحسين شكل خانة الاسم */
div[data-baseweb="input"] { direction: rtl; }
</style>
""", unsafe_allow_html=True)

# ── Auth Function ────────────────────────────────────────────────────────────
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
                st.error("❌ ملف credentials.json مش موجود!")
                st.stop()
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("drive", "v3", credentials=creds)

def upload_and_share(service, file_bytes, filename, mime_type):
    media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type, resumable=True)
    uploaded = service.files().create(
        body={"name": filename, "parents": [FOLDER_ID]},
        media_body=media,
        fields="id,webViewLink"
    ).execute()
    service.permissions().create(fileId=uploaded["id"], body={"type": "anyone", "role": "reader"}).execute()
    result = service.files().get(fileId=uploaded["id"], fields="webViewLink").execute()
    return result["webViewLink"]

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown('<div class="title">☁️ ارفع صورة على Drive</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">ارفع ملف أو الصق صورة مباشرة (Paste)</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    uploaded_file = st.file_uploader("اختار صورة", type=["png", "jpg", "jpeg", "webp"])

with col2:
    st.write("أو الصق صورة من الكليبورد")
    pasted_image = paste_image_button("📋 اضغط هنا للصق (Paste)")

# متغيرات الصورة
final_image_bytes = None
original_name = "uploaded_image.png"
mime_type = "image/png"

if uploaded_file:
    final_image_bytes = uploaded_file.read()
    original_name = uploaded_file.name
    mime_type = uploaded_file.type
    st.image(Image.open(io.BytesIO(final_image_bytes)), caption="معاينة الملف المختار", use_container_width=True)

elif pasted_image and pasted_image.image_data is not None:
    img_buffer = io.BytesIO()
    pasted_image.image_data.save(img_buffer, format="PNG")
    final_image_bytes = img_buffer.getvalue()
    st.image(pasted_image.image_data, caption="معاينة الصورة الملصقة", use_container_width=True)

# ── الجزء الجديد: تسمية الصورة والرفع ──
if final_image_bytes:
    st.markdown("---")
    # خانة الاسم الجديدة
    custom_name = st.text_input("📝 اختار اسم للصورة (اختياري)", placeholder="مثلاً: مسألة_تفاضل_1")
    
    if st.button("☁️ ارفع وجيب اللينك"):
        with st.spinner("جاري الرفع..."):
            try:
                service = get_drive_service()
                
                # تحديد الاسم النهائي
                if custom_name.strip():
                    final_name = f"{custom_name.strip()}.png"
                else:
                    final_name = original_name
                
                link = upload_and_share(service, final_image_bytes, final_name, mime_type)
                
                st.markdown('<div class="link-box">', unsafe_allow_html=True)
                st.markdown(f'<div class="link-label">✅ تم الرفع باسم: {final_name}</div>', unsafe_allow_html=True)
                st.code(link, language=None)
                st.markdown('</div>', unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"حصل خطأ: {e}")
