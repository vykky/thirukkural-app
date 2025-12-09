import streamlit as st
import json
import os
import google.generativeai as genai
import time

# --- 1. பக்கம் வடிவமைப்பு ---
st.set_page_config(page_title="திருக்குறள் மின்னுலகம்", layout="centered", page_icon="✨")

# --- 2. CSS டிசைன் ---
st.markdown("""
    <style>
    /* தலைப்பு */
    h1 {
        color: #2e7d32;
        text-align: center;
        font-family: sans-serif;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }

    /* --- CHAT INPUT FIX (Moves input box UP above footer) --- */
    [data-testid="stBottom"] {
        bottom: 80px !important; /* Increased to clear footer */
        background-color: transparent !important;
        z-index: 1000;
    }

    /* Chat Input Styling */
    .stChatInput textarea {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #2e7d32 !important;
        border-radius: 10px !important;
    }

    /* General Input Box */
    .stTextInput input {
        background-color: #ffffff !important;
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 10px;
        font-weight: bold;
    }
    .stTextInput input:focus { border-color: #2e7d32; }
    
    /* Label Bold */
    .stTextInput label {
        font-weight: 900 !important;
        color: #1b5e20 !important;
        font-size: 16px;
    }

    /* Custom Boxes */
    .verdict-box { background-color: #fff3e0; padding: 15px; border-radius: 10px; border-left: 6px solid #ff9800; color: #e65100; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .verdict-label { font-size: 18px; font-weight: 900; display: block; margin-bottom: 5px; color: #ef6c00; }
    .verdict-text { font-size: 19px; font-weight: bold; }

    /* Kural Card */
    .kural-card {
        background-color: #ffffff; padding: 20px; border-radius: 12px; border: 1px solid #e8f5e9; border-left: 6px solid #2e7d32;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08); margin-bottom: 20px; margin-top: 20px;
    }
    
    /* Header Style: Number + Adhigaaram */
    .kural-header {
        background-color: #ffe0b2;
        color: #e65100;
        padding: 6px 15px;
        border-radius: 20px;
        font-size: 15px;
        font-weight: 900;
        display: inline-block;
        margin-bottom: 15px;
    }

    .kural-text { font-size: 22px; font-weight: 900; color: #1b5e20; margin-bottom: 6px; font-family: sans-serif; line-height: 1.5; }
    
    /* Meaning Box & Bold Label Fix */
    .meaning-box { margin-top: 15px; font-size: 17px; color: #424242; line-height: 1.6; padding-top: 10px; border-top: 1px dashed #c8e6c9; }
    .meaning-label { 
        font-weight: 900 !important; 
        color: #1b5e20 !important; 
        font-size: 16px;
        text-transform: uppercase;
    }
    
    .solution-box { background-color: #e3f2fd; padding: 15px; border-radius: 10px; border-left: 6px solid #1565c0; color: #0d47a1; margin-top: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
    .solution-label { font-size: 18px; font-weight: 900; display: block; margin-bottom: 5px; color: #1565c0; }
    .solution-text { font-size: 17px; font-weight: 500; line-height: 1.8; text-align: justify; }

    /* Footer - Fixed at absolute bottom */
    .footer {
        position: fixed;
        left: 0;
        bottom: 0;
        width: 100%;
        height: 70px;
        background-color: #c5e1a5; 
        color: #1b5e20;
        text-align: center;
        padding-top: 15px;
        font-size: 13px;
        border-top: 3px solid #2e7d32;
        z-index: 9999;
    }
    
    div.block-container { padding-bottom: 160px; }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>✨ திருக்குறள் மின்னுலகம் ✨</h1>", unsafe_allow_html=True)
st.caption("v1.0 | நவீன தமிழ் தொழில்நுட்பம்")

# --- 3. API Key & Robust Model Setup (NEW KEY APPLIED HERE) ---
if "GEMINI_API_KEY" in st.secrets:
    GOOGLE_API_KEY = st.secrets["GEMINI_API_KEY"]
else:
    # 🟢 புதிய கீ வெற்றிகரமாக சேர்க்கப்பட்டது!
    GOOGLE_API_KEY = "AIzaSyBpsr86YG8FJJJQPJto5MNmCy6ISLGhbZs" 

@st.cache_resource
def get_gemini_model():
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                return genai.GenerativeModel(m.name)
        return None
    except:
        return None

model = get_gemini_model()

# --- 4. டேட்டா லோட் & அதிகாரப் பெயர் கண்டுபிடித்தல் ---
@st.cache_data
def load_data():
    file_path = 'thirukkural.json'
    if not os.path.exists(file_path): return []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                return data.get("kural", data.get("kurals", []))
            return data
    except: return []

kurals_list = load_data()

def get_adhigaaram(item):
    keys = ['adhigaaram', 'Adhigaram', 'adikaram', 'Chapter', 'chapter', 'paul_name', 'iyal']
    for k in keys:
        val = item.get(k)
        if val: return val
    return "பொது"

# --- மெனு ---
selected_option = st.radio("", ["🔍 குறள் தேடல்", "⚖️ சூழல் தீர்ப்பு", "🤖 AI வள்ளுவர்"], horizontal=True)
st.divider()

# ==================================================
# 1. குறள் தேடல் 
# ==================================================
if selected_option == "🔍 குறள் தேடல்":
    search_term = st.text_input("தேட வேண்டிய சொல்:", placeholder="எ.கா: நட்பு, முயற்சி")
    if st.button("தேடு"):
        if kurals_list and search_term:
            results = []
            for k in kurals_list:
                full_text = f"{k.get('Line1','')} {k.get('Line2','')} {k.get('mv','')} {k.get('sp','')} {k.get('mk','')}"
                if search_term in full_text:
                    results.append(k)
            if results:
                st.success(f"✅ {len(results)} குறள்கள் கிடைத்தன:")
                for item in results:
                    adh_name = get_adhigaaram(item)
                    
                    st.markdown(f"""
                    <div class="kural-card">
                        <div class="kural-header">
                            📖 குறள்: {item.get('Number', '')} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 அதிகாரம்: {adh_name}
                        </div>
                        <div class="kural-text">{item.get('Line1', '')}</div>
                        <div class="kural-text">{item.get('Line2', '')}</div>
                        <div class="meaning-box">
                            <span class="meaning-label">💡 விளக்கம்:</span><br>{item.get('mv', '')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning("குறள் இல்லை.")

# ==================================================
# 2. சூழல் தீர்ப்பு
# ==================================================
elif selected_option == "⚖️ சூழல் தீர்ப்பு":
    user_input = st.text_input("கேள்வி (எ.கா: கடன் வாங்கலாமா?):")
    
    if st.button("தீர்ப்பு வழங்கு"):
        if not user_input:
            st.warning("கேள்வியைத் டைப் செய்யவும்.")
        elif not model:
            st.error("AI இணைப்பு இல்லை (புதிய API Key-ஐ சரிபார்க்கவும்).")
        else:
            with st.spinner("👨‍🦳 திருவள்ளுவர் ஆராய்கிறார்..."):
                try:
                    prompt = f"""
                    சூழல்: '{user_input}'
                    
                    JSON வடிவில் மட்டும் பதில் தா.
                    Format:
                    {{
                        "verdict": "அறிவுரை (ஒரே வரியில், Bold)",
                        "aram": 50, "porul": 50, "inbam": 50,
                        "kural_line1": "...", "kural_line2": "...",
                        "kural_explanation": "...",
                        "adhigaaram": "அதிகாரம் பெயர்", 
                        "kural_number": "எண்"
                    }}
                    """
                    response = model.generate_content(prompt)
                    text_resp = response.text.replace("```json", "").replace("```", "").strip()
                    res = json.loads(text_resp)
                    
                    st.warning(f"📢 **அறிவுரை:** {res.get('verdict')}")

                    c1, c2, c3 = st.columns(3)
                    c1.metric("அறம்", f"{res.get('aram')}%")
                    c2.metric("பொருள்", f"{res.get('porul')}%")
                    c3.metric("இன்பம்", f"{res.get('inbam')}%")
                    
                    st.write("")

                    adh_name = res.get('adhigaaram', 'பொது')
                    
                    st.markdown(f"""
                    <div class="kural-card">
                        <div class="kural-header">
                            📖 குறள்: {res.get('kural_number')} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 அதிகாரம்: {adh_name}
                        </div>
                        <div class="kural-text">{res.get('kural_line1')}</div>
                        <div class="kural-text">{res.get('kural_line2')}</div>
                        <div class="meaning-box">
                            <span class="meaning-label">💡 விளக்கம்:</span><br>{res.get('kural_explanation')}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                        
                except Exception as e:
                    if "403" in str(e):
                        st.error("❌ பிழை: API Key முடக்கப்பட்டுள்ளது.")
                    elif "429" in str(e):
                        st.error("⚠️ வள்ளுவர் ஓய்வெடுக்கிறார் (Quota Exceeded).")
                    else:
                        st.error(f"பிழை: {e}")

# ==================================================
# 3. AI வள்ளுவர்
# ==================================================
elif selected_option == "🤖 AI வள்ளுவர்":
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "வாழ்க வளமுடன்! நான் திருவள்ளுவர் பேசுகிறேன். உங்களின் வாழ்வியல் சந்தேகங்களை என்னிடம் கேளுங்கள்."
        }]

    for message in st.session_state.messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            if role == "assistant" and "{" in message["content"]:
                try:
                    r = json.loads(message["content"])
                    st.warning(f"📢 **அறிவுரை:** {r.get('verdict')}")
                    
                    adh_name = r.get('adhigaaram', 'பொது')
                    
                    st.markdown(f"""
                    <div class="kural-card">
                        <div class="kural-header">
                            📖 குறள்: {r.get('kural_number')} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 அதிகாரம்: {adh_name}
                        </div>
                        <div class="kural-text">{r.get('kural_line1')}</div>
                        <div class="kural-text">{r.get('kural_line2')}</div>
                        <div class="meaning-box">
                            <span class="meaning-label">💡 விளக்கம்:</span><br>{r.get('kural_explanation')}
                        </div>
                    </div>
                    <div class="solution-box"><span class="solution-label">✅ தீர்வு:</span><div class="solution-text">{r.get('solution')}</div></div>
                    """, unsafe_allow_html=True)
                except:
                    st.write(message["content"])
            else:
                st.write(message["content"])

    if prompt := st.chat_input("வள்ளுவரிடம் கேட்க..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if model:
            with st.spinner("👨‍🦳 திருவள்ளுவர் ஆராய்கிறார்..."):
                try:
                    sys_msg = """
                    நீ திருவள்ளுவர். JSON வடிவில் பதில் அளி.
                    Format:
                    {
                        "verdict": "அறிவுரை (ஒரே வரியில்)",
                        "kural_line1": "குறள் வரி 1",
                        "kural_line2": "குறள் வரி 2",
                        "kural_explanation": "விளக்கம்",
                        "solution": "தீர்வு (சுருக்கமாக)",
                        "adhigaaram": "அதிகாரம்",
                        "kural_number": "எண்"
                    }
                    """
                    response = model.generate_content(sys_msg + "\n\nகேள்வி: " + prompt)
                    text_resp = response.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.messages.append({"role": "assistant", "content": text_resp})
                    
                    res = json.loads(text_resp)
                    with st.chat_message("assistant"):
                        st.warning(f"📢 **அறிவுரை:** {res.get('verdict')}")
                        
                        adh_name = res.get('adhigaaram', 'பொது')
                        
                        st.markdown(f"""
                        <div class="kural-card">
                            <div class="kural-header">
                                📖 குறள்: {res.get('kural_number')} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 அதிகாரம்: {adh_name}
                            </div>
                            <div class="kural-text">{res.get('kural_line1')}</div>
                            <div class="kural-text">{res.get('kural_line2')}</div>
                            <div class="meaning-box">
                                <span class="meaning-label">💡 விளக்கம்:</span><br>{res.get('kural_explanation')}
                            </div>
                        </div>
                        <div class="solution-box"><span class="solution-label">✅ தீர்வு:</span><div class="solution-text">{res.get('solution')}</div></div>
                        """, unsafe_allow_html=True)
                except Exception as e:
                    if "403" in str(e):
                        st.error("❌ பிழை: API Key முடக்கப்பட்டுள்ளது.")
                    else:
                        st.error("பிழை.")

# --- FOOTER (Fixed at Bottom) ---
st.markdown("""
    <div class="footer">
        <p>© All rights reserved by <span style="font-weight:900; color:black;">MIN E KAVI (மின் கவி)</span></p>
        <p>Developed & Designed by <span style="font-weight:900; color:black;">VIGNESH M</span> | FOUNDER OF MIN E KAVI</p>
    </div>
""", unsafe_allow_html=True)
