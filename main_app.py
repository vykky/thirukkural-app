import streamlit as st
import json
import os
import google.generativeai as genai
import streamlit.components.v1 as components

# --- 1. பக்கம் வடிவமைப்பு ---
st.set_page_config(page_title="திருக்குறள் மின்னுலகம்", layout="centered", page_icon="✨")

# --- 2. CSS டிசைன் ---
st.markdown("""
    <style>
    h1 { color: #2e7d32; text-align: center; font-family: 'Helvetica', sans-serif; text-shadow: 1px 1px 2px rgba(0,0,0,0.1); margin-bottom: 20px; }
    
    div[role="radiogroup"] { background-color: #f1f8e9; padding: 10px; border-radius: 15px; border: 2px solid #a5d6a7; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; justify-content: center; flex-wrap: wrap; gap: 10px; margin-bottom: 20px; }
    div[role="radiogroup"] label { font-weight: 900 !important; font-size: 16px !important; color: #1b5e20 !important; background-color: white; padding: 8px 15px; border-radius: 10px; border: 1px solid #c8e6c9; margin: 0 !important; cursor: pointer; transition: all 0.3s; }
    div[role="radiogroup"] label:hover { background-color: #c8e6c9; }

    .stChatInput textarea, .stTextInput > div > div > input { background-color: #ffffff !important; color: #000000 !important; border: 2px solid #4caf50 !important; border-radius: 15px !important; }
    .stChatInput textarea:focus, .stTextInput > div > div > input:focus { border-color: #1b5e20 !important; box-shadow: 0 0 10px rgba(46, 125, 50, 0.2); }

    [data-testid="stChatMessage"] { padding: 1rem; border-radius: 15px; margin-bottom: 1rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); width: 90%; display: flex; flex-direction: column; }
    [data-testid="stChatMessage"][data-testid="stChatMessageUser"] { margin-left: auto; background-color: #e8f5e9; border: 1px solid #c5e1a5; text-align: right; align-items: flex-end; }
    [data-testid="stChatMessage"][data-testid="stChatMessageAssistant"] { margin-right: auto; background-color: #ffffff; border: 1px solid #e0e0e0; text-align: left; align-items: flex-start; }

    .result-box { padding: 15px; border-radius: 12px; margin-bottom: 18px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); width: 100%; text-align: left; }
    .box-advice { background-color: #e3f2fd; border: 1px solid #90caf9; border-left: 5px solid #1976d2; }
    .box-kural { background-color: #e8f5e9; border: 1px solid #a5d6a7; border-left: 5px solid #2e7d32; }
    .box-solution { background-color: #fffde7; border: 1px solid #fff59d; border-left: 5px solid #fbc02d; }
    .box-consequence { background-color: #ffebee; border: 1px solid #ef9a9a; border-left: 5px solid #c62828; }
    
    .box-header { font-family: 'Georgia', serif; font-size: 18px; font-weight: 900; margin-bottom: 8px; display: block; letter-spacing: 0.5px; }
    .label-advice { color: #1565c0; } .label-solution { color: #f57f17; } .label-consequence { color: #c62828; }
    .box-text { font-family: 'Verdana', sans-serif; font-size: 16px; line-height: 1.6; text-align: justify; font-weight: 500; color: #333; }

    .percentage-container { display: flex; flex-wrap: wrap; justify-content: space-around; background-color: #f1f8e9; border: 2px solid #a5d6a7; border-radius: 15px; padding: 15px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .percentage-item { font-size: 20px; font-weight: 900; margin: 5px; white-space: nowrap; }

    .kural-meta { background-color: #c8e6c9; color: #1b5e20; padding: 4px 12px; border-radius: 12px; font-size: 13px; font-weight: bold; display: inline-block; margin-bottom: 10px; }
    .kural-font { font-size: 19px; font-weight: 900; color: #1b5e20; line-height: 1.5; font-family: 'Times New Roman', serif; }
    .kural-meaning { margin-top: 10px; font-size: 16px; color: #33691e; border-top: 1px dashed #a5d6a7; padding-top: 8px; font-weight: bold; text-align: left;}

    [data-testid="stBottom"] { bottom: 60px !important; background-color: transparent !important; z-index: 1000; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; height: 60px; background-color: #c5e1a5; color: #1b5e20; text-align: center; padding: 5px 0; border-top: 3px solid #2e7d32; z-index: 2000; box-shadow: 0 -2px 10px rgba(0,0,0,0.1); display: flex; flex-direction: column; justify-content: center; }
    .footer p { margin: 2px 0 !important; font-size: 12px; font-weight: bold; line-height: 1.3; }
    div.block-container { padding-bottom: 150px; }
    footer {visibility: hidden;} header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 3. SCROLL SCRIPT ---
scroll_script = """
<script>
    function setupScrollListener() {
        var chatInput = window.parent.document.querySelector('[data-testid="stBottom"]');
        if(chatInput) { chatInput.style.opacity = '1'; }
    }
    setTimeout(setupScrollListener, 1000);
</script>
"""
components.html(scroll_script, height=0, width=0)

st.markdown("<h1>✨ திருக்குறள் மின்னுலகம் ✨</h1>", unsafe_allow_html=True)

# --- 4. API & Config (SMART AUTO-SELECT MODEL) ---
# புதிய KEY இங்கே உள்ளது
GOOGLE_API_KEY = "AIzaSyDkUlugUApJBhv4CNgZXMt1adyb1CNqlDc"

@st.cache_resource
def load_smart_model(api_key):
    try:
        genai.configure(api_key=api_key)
        
        # 1. API-ல் உள்ள அனைத்து மாடல்களையும் பட்டியலிடு
        available_models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name)
        except:
            pass

        # 2. முன்னுரிமை: Flash > Pro > Others
        # பெயரில் 'flash' உள்ளதா எனத் தேடுகிறது (சரியான பெயரை எடுக்க)
        for m_name in available_models:
            if "flash" in m_name.lower():
                return genai.GenerativeModel(m_name)
        
        for m_name in available_models:
            if "pro" in m_name.lower():
                return genai.GenerativeModel(m_name)

        # 3. எதுவும் கிடைக்கவில்லை என்றால், பட்டியலில் உள்ள முதல் மாடலை எடு
        if available_models:
            return genai.GenerativeModel(available_models[0])
            
        # 4. பட்டியல் வரவில்லை என்றால் Default பெயரை முயற்சி செய்
        return genai.GenerativeModel("gemini-pro") 
    except: return None

model = load_smart_model(GOOGLE_API_KEY)

# --- 5. DATA LOADING & HELPERS ---
ADHIGAARAM_MAP = {
    1: "கடவுள் வாழ்த்து", 2: "வான்சிறப்பு", 3: "நீத்தார் பெருமை", 4: "அறன் வலியுறுத்தல்", 5: "இல்வாழ்க்கை",
    6: "வாழ்க்கைத் துணைநலம்", 7: "மக்கட்பேறு", 8: "அன்புடைமை", 9: "விருந்தோம்பல்", 10: "இனியவை கூறல்",
    11: "செய்ந்நன்றி அறிதல்", 12: "நடுவு நிலைமை", 13: "அடக்க முடைமை", 14: "ஒழுக்க முடைமை", 15: "பிறனில் விழையாமை",
    16: "பொறையுடைமை", 17: "அழுக்காறாமை", 18: "வெஃகாமை", 19: "புறங்கூறாமை", 20: "பயனில சொல்லாமை",
    21: "தீவினையச்சம்", 22: "ஒப்புரவறிதல்", 23: "ஈகை", 24: "புகழ்", 25: "அருளுடைமை",
    26: "புலால் மறுத்தல்", 27: "தவம்", 28: "கூடா ஒழுக்கம்", 29: "கள்ளாமை", 30: "வாய்மை",
    31: "வெகுளாமை", 32: "இன்னா செய்யாமை", 33: "கொல்லாமை", 34: "நிலையாமை", 35: "துறவு",
    36: "மெய்யுணர்தல்", 37: "அவா அறுத்தல்", 38: "ஊழ்", 39: "இறைமாட்சி", 40: "கல்வி",
    41: "கல்லாமை", 42: "கேள்வி", 43: "அறிவுடைமை", 44: "குற்றங்கடிதல்", 45: "பெரியாரைத் துணைக்கோடல்",
    46: "சிற்றினம் சேராமை", 47: "தெரிந்து செயல்வகை", 48: "வலியறிதல்", 49: "காலமறிதல்", 50: "இடனறிதல்",
    51: "தெரிந்து தெளிதல்", 52: "தெரிந்து வினையாடல்", 53: "சுற்றந்தழால்", 54: "பொச்சாவாமை", 55: "செங்கோன்மை",
    56: "கொடுங்கோன்மை", 57: "வெருவந்த செய்யாமை", 58: "கண்ணோட்டம்", 59: "ஒற்றாடல்", 60: "ஊக்கம் உடைமை",
    61: "மடியின்மை", 62: "ஆள்வினையுடைமை", 63: "இடுக்கண் அழியாமை", 64: "அமைச்சு", 65: "சொல்வன்மை",
    66: "வினைத்திட்பம்", 67: "வினைசெயல்வகை", 68: "தூது", 69: "மன்னரைச் சேர்ந்தொழுகல்", 70: "குறிப்பறிதல்",
    71: "அவை அறிதல்", 72: "அவை அஞ்சாமை", 73: "கல்வி", 74: "நாடு", 75: "அரண்",
    76: "பொருள்செயல்வகை", 77: "படைமாட்சி", 78: "படைச்செருக்கு", 79: "நட்பு", 80: "நட்பாராய்தல்",
    81: "பழைமை", 82: "தீநட்பு", 83: "கூடாநட்பு", 84: "பேதைமை", 85: "புல்லறிவாண்மை",
    86: "இகல்", 87: "பகைமாட்சி", 88: "பகைத்திறம் தெரிதல்", 89: "உட்பகை", 90: "பெரியாரைப் பிழையாமை",
    91: "பெண்வழிச் சேறல்", 92: "வரைவின் மகளிர்", 93: "கள்ளுண்ணாமை", 94: "சூது", 95: "மருந்து",
    96: "குடிமை", 97: "மானம்", 98: "பெருமை", 99: "சான்றாண்மை", 100: "பண்புடைமை",
    101: "நன்றியில் செல்வம்", 102: "நாணுடைமை", 103: "குடிசெயல்வகை", 104: "உழவு", 105: "நல்குரவு",
    106: "இரவு", 107: "இரவச்சம்", 108: "கயமை", 109: "தகைனணங்குறுத்தல்", 110: "குறிப்பறிதல்",
    111: "புணர்ச்சி மகிழ்தல்", 112: "நலம் புனைந்து உரைத்தல்", 113: "காதல் சிறப்புரைத்தல்", 114: "நாணுத் துறவுரைத்தல்", 115: "அலர் அறிவுறுத்தல்",
    116: "பிரிவு ஆற்றாமை", 117: "படர்மெலிிரங்கல்", 118: "கண்விதுப்பழிதல்", 119: "பசப்புறு பருவரல்", 120: "தனிப்படர் மிகுதி",
    121: "நினைந்தவர் புலம்பல்", 122: "கனவுநிலையுரைத்தல்", 123: "பொழுதுகண்டிரங்கல்", 124: "உறுப்புநலனழிதல்", 125: "நெஞ்சொடு கிளத்தல்",
    126: "நிறையழிதல்", 127: "அவர்வயின் விதும்பல்", 128: "குறிப்பறிவுறுத்தல்", 129: "புணர்ச்சி விதும்பல்", 130: "நெஞ்சொடு புலத்தல்",
    131: "புலவி", 132: "புலவி நுணுக்கம்", 133: "ஊடலுவகை"
}

SMART_SEARCH_MAP = {
    "வங்கி": ["பொருள்", "செல்வம்", "ஈட்டல்", "சேமிப்பு"],
    "பணம்": ["பொருள்", "செல்வம்", "நல்குரவு"],
    "ஏடிஎம்": ["பொருள்", "செல்வம்"],
    "பள்ளி": ["கல்வி", "அறிவு", "கற்பவை"],
    "கல்லூரி": ["கல்வி", "அறிவு", "சான்றோன்"],
    "நூலகம்": ["கல்வி", "கேள்வி", "அறிவு"],
    "சுற்றுலா": ["இன்பம்", "காலம்", "பொருள்"], 
    "பயணம்": ["ஊக்கம்", "வினை", "காலம்"],
    "மருத்துவமனை": ["மருந்து", "நோய்", "பிணி"],
    "டாக்டர்": ["மருந்து", "மருத்துவன்"],
    "வீடு": ["இல்வாழ்க்கை", "மனை", "அன்பு", "விருந்தோம்பல்"],
    "குடும்பம்": ["சுற்றம்", "அன்பு", "மக்கள்"],
    "அலுவலகம்": ["வினை", "முயற்சி", "ஆள்வினை"],
    "வேலை": ["வினை", "தொழில்", "முயற்சி"],
    "நீதிமன்றம்": ["நடுவுநிலைமை", "முறை", "செங்கோன்மை"],
    "போலீஸ்": ["ஒற்று", "காவல்", "அரண்"],
    "காவல்": ["அரண்", "காப்பு"],
    "விவசாயம்": ["உழவு", "மாரி", "வான்"]
}

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

def get_adhigaaram_text(item):
    try:
        num_str = item.get('Number', item.get('no', 0))
        num = int(num_str)
        if num > 0:
            chap_num = (num - 1) // 10 + 1
            chap_name = ADHIGAARAM_MAP.get(chap_num, "பொது")
            return f"அதிகாரம் {chap_num}: {chap_name}"
    except:
        pass
    return "பொது"

def extract_json_from_text(text):
    try:
        text = text.strip()
        start_idx = text.find('{')
        end_idx = text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx : end_idx + 1]
            return json.loads(json_str)
        return None
    except:
        return None

# --- 6. MENU (RESPONSIVE) ---

selected_option = st.radio(
    "", 
    ["🔍 குறள் தேடல்", "⚖️ சூழல் தீர்ப்பு", "🤖 AI வள்ளுவர்"], 
    horizontal=True
)

st.divider()

# ==================================================
# 1. குறள் தேடல்
# ==================================================
if selected_option == "🔍 குறள் தேடல்":
    search_term = st.text_input("தேட வேண்டிய சொல் / இடம் / எண்:", placeholder="எ.கா: வங்கி, பள்ளி, 10, அன்பு")
    
    if st.button("தேடு"):
        if kurals_list and search_term:
            results = []
            query_words = []
            is_smart_search = False
            
            if search_term in SMART_SEARCH_MAP:
                query_words = SMART_SEARCH_MAP[search_term]
                is_smart_search = True
                mapped_str = ", ".join(query_words)
                st.info(f"💡 **Smart Search:** நீங்கள் தேடிய **'{search_term}'** என்ற சொல்லுக்காக **'{mapped_str}'** தொடர்பான குறள்கள் தேடப்படுகின்றன.")
            else:
                query_words = [search_term]
            
            for k in kurals_list:
                full_text = f"{k.get('Line1','')} {k.get('Line2','')} {k.get('mv','')} {k.get('mk','')} {k.get('sp','')}"
                k_num = str(k.get('Number', k.get('no', '0')))
                if search_term == k_num:
                    results.append(k)
                    break 
                
                for q in query_words:
                    if q in full_text:
                        results.append(k)
                        break 

            if results:
                if is_smart_search and len(results) > 20:
                    st.success(f"✅ **'{search_term}'** தொடர்புடைய {len(results)} குறள்கள் கிடைத்தன (முதல் 10 மட்டும் கீழே):")
                    results = results[:10]
                else:
                    st.success(f"✅ {len(results)} குறள்கள் கிடைத்தன:")
                
                for item in results:
                    adh_text = get_adhigaaram_text(item) 
                    kural_num = item.get('Number', item.get('no', 'Unknown'))
                    
                    header_txt = f"📖 குறள் எண்: {kural_num} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 {adh_text}"

                    st.markdown(f"""
                    <div class="result-box box-kural">
                        <div class="kural-meta">{header_txt}</div>
                        <div class="kural-font">{item.get('Line1', '')}</div>
                        <div class="kural-font">{item.get('Line2', '')}</div>
                        <div class="kural-meaning"><b>💡 விளக்கம்:</b><br>{item.get('mv', item.get('mk', 'விளக்கம் இல்லை'))}</div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.warning(f"'{search_term}' தொடர்புடைய குறள் எதுவும் இல்லை.")

# ==================================================
# 2. சூழல் தீர்ப்பு
# ==================================================
elif selected_option == "⚖️ சூழல் தீர்ப்பு":
    user_input = st.text_input("கேள்வி (எ.கா: கடன் வாங்கலாமா?):")
    
    if st.button("தீர்ப்பு வழங்கு"):
        if not user_input:
            st.warning("கேள்வியைத் டைப் செய்யவும்.")
        elif not model:
            st.error("AI இணைப்பு இல்லை.")
        else:
            with st.spinner("📜 வள்ளுவன் கணிக்கிறார்..."):
                try:
                    prompt = f"""
                    சூழல்: '{user_input}'
                    JSON வடிவில் மட்டும் பதில் தா.
                    முக்கியம்: 'aram', 'porul', 'inbam' கூட்டுத்தொகை சரியாக 100 வர வேண்டும்.
                    
                    Format:
                    {{
                        "verdict": "அறிவுரை (ஒரே வரியில், தெளிவாக)",
                        "aram": 40, "porul": 40, "inbam": 20,
                        "kural_line1": "முதல் வரி...", "kural_line2": "இரண்டாம் வரி...",
                        "kural_explanation": "தெளிவான விளக்கம்...",
                        "adhigaaram": "அதிகார பெயர் மட்டும்", 
                        "kural_number": "எண் (எ.கா: 781)"
                    }}
                    """
                    response = model.generate_content(prompt)
                    res = extract_json_from_text(response.text)
                    
                    if res:
                        st.markdown(f"""
                        <div class="result-box box-advice">
                            <span class="box-header label-advice">📢 அறிவுரை:</span>
                            <div class="box-text">{res.get('verdict')}</div>
                        </div>
                        """, unsafe_allow_html=True)

                        aram = res.get('aram')
                        porul = res.get('porul')
                        inbam = res.get('inbam')
                        
                        # --- PERCENTAGE DISPLAY ---
                        st.markdown(f"""
                        <div class="percentage-container">
                            <span class="percentage-item" style="color: #2e7d32;">⚖️ அறம்: {aram}%</span>
                            <span class="percentage-item" style="color: #f9a825;">💰 பொருள்: {porul}%</span>
                            <span class="percentage-item" style="color: #c62828;">❤️ இன்பம்: {inbam}%</span>
                        </div>
                        """, unsafe_allow_html=True)

                        try:
                            k_num = int(''.join(filter(str.isdigit, str(res.get('kural_number', '0')))))
                            if k_num > 0:
                                c_num = (k_num - 1) // 10 + 1
                                adh_name = ADHIGAARAM_MAP.get(c_num, res.get('adhigaaram', 'பொது'))
                                final_adh_str = f"அதிகாரம் {c_num}: {adh_name}"
                            else: final_adh_str = res.get('adhigaaram', 'பொது')
                        except: final_adh_str = res.get('adhigaaram', 'பொது')

                        header_txt = f"📖 குறள் எண்: {res.get('kural_number')} &nbsp;&nbsp;|&nbsp;&nbsp; 📂 {final_adh_str}"
                        
                        st.markdown(f"""
                        <div class="result-box box-kural">
                            <div class="kural-meta">{header_txt}</div>
                            <div class="kural-font">{res.get('kural_line1')}</div>
                            <div class="kural-font">{res.get('kural_line2')}</div>
                            <div class="kural-meaning"><b>💡 விளக்கம்:</b><br>{res.get('kural_explanation')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.error("AI பதிலில் பிழை ஏற்பட்டது. மீண்டும் முயற்சிக்கவும்.")
                        
                except Exception as e:
                    st.error(f"பிழை: {e}")

# ==================================================
# 3. AI வள்ளுவர் (IMPROVED CHAT)
# ==================================================
elif selected_option == "🤖 AI வள்ளுவர்":
    
    if "messages" not in st.session_state:
        st.session_state.messages = [{
            "role": "assistant", 
            "content": "வாழ்க வளமுடன்! யாம் திருவள்ளுவன். உமது சிந்தனைகளையும், ஐயங்களையும் என்னிடம் பகிர்க. குறள் வழி தீர்வு நல்குகிறேன்."
        }]

    for message in st.session_state.messages:
        role = "assistant" if message["role"] == "assistant" else "user"
        with st.chat_message(role):
            if role == "assistant" and "{" in message["content"]:
                r = extract_json_from_text(message["content"])
                if r:
                    try:
                        k_num = int(r.get('kural_number', 0))
                        if k_num > 0:
                            c_num = (k_num - 1) // 10 + 1
                            adh_name = r.get('adhigaaram', 'பொது')
                            final_adh = f"அதிகாரம் {c_num}: {adh_name}"
                        else: final_adh = r.get('adhigaaram', 'பொது')
                    except: final_adh = r.get('adhigaaram')

                    st.markdown(f"""
                    <div class="result-box box-advice">
                        <span class="box-header label-advice">📢 அறிவுரை:</span>
                        <div class="box-text">{r.get('verdict')}</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="result-box box-kural">
                        <div class="kural-meta">📖 குறள்: {r.get('kural_number')} &nbsp;|&nbsp; 📂 {final_adh}</div>
                        <div class="kural-font">{r.get('kural_line1')}</div>
                        <div class="kural-font">{r.get('kural_line2')}</div>
                        <div class="kural-meaning"><b>💡 விளக்கம்:</b> {r.get('kural_explanation')}</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="result-box box-solution">
                        <span class="box-header label-solution">✅ வள்ளுவர் தீர்வு:</span>
                        <div class="box-text">{r.get('solution')}</div>
                    </div>""", unsafe_allow_html=True)

                    st.markdown(f"""
                    <div class="result-box box-consequence">
                        <span class="box-header label-consequence">⚠️ இதை மீறினால்:</span>
                        <div class="box-text">{r.get('consequence')}</div>
                    </div>""", unsafe_allow_html=True)
                else:
                    st.write(message["content"])
            else:
                st.write(message["content"])

    if prompt := st.chat_input("வள்ளுவரிடம் கேட்க..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)

        if model:
            with st.spinner("📜 வள்ளுவன் வாக்கு..."):
                try:
                    sys_msg = f"""
                    நீ திருவள்ளுவர். நீ ஒரு AI அல்ல, நீ ஒரு தமிழ் முனிவர்.
                    பயனர் கேட்கும் கேள்விக்கு நேரடியாக, தெளிவாக, ஆனால் அன்பாக பதில் சொல்.
                    
                    பதில் கண்டிப்பாக கீழே உள்ள JSON வடிவில் மட்டுமே இருக்க வேண்டும்.
                    
                    JSON Format:
                    {{
                        "verdict": "ஒரே வரியில் அறிவுரை",
                        "kural_line1": "குறள் வரி 1",
                        "kural_line2": "குறள் வரி 2",
                        "kural_explanation": "குறள் விளக்கம்",
                        "kural_number": "எண் (எ.கா: 100)",
                        "adhigaaram": "அதிகாரப் பெயர்",
                        "solution": "விரிவான தீர்வு (50 words)",
                        "consequence": "இதை மீறினால் ஏற்படும் விளைவு"
                    }}
                    """
                    
                    response = model.generate_content(sys_msg + "\n\nகேள்வி: " + prompt)
                    text_resp = response.text
                    st.session_state.messages.append({"role": "assistant", "content": text_resp})
                    r = extract_json_from_text(text_resp)
                    
                    if r:
                        try:
                            k_num = int(r.get('kural_number', 0))
                            if k_num > 0:
                                c_num = (k_num - 1) // 10 + 1
                                adh_name = r.get('adhigaaram', 'பொது')
                                final_adh = f"அதிகாரம் {c_num}: {adh_name}"
                            else: final_adh = r.get('adhigaaram', 'பொது')
                        except: final_adh = r.get('adhigaaram')

                        with st.chat_message("assistant"):
                            st.markdown(f"""
                            <div class="result-box box-advice">
                                <span class="box-header label-advice">📢 அறிவுரை:</span>
                                <div class="box-text">{r.get('verdict')}</div>
                            </div>""", unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="result-box box-kural">
                                <div class="kural-meta">📖 குறள்: {r.get('kural_number')} &nbsp;|&nbsp; 📂 {final_adh}</div>
                                <div class="kural-font">{r.get('kural_line1')}</div>
                                <div class="kural-font">{r.get('kural_line2')}</div>
                                <div class="kural-meaning"><b>💡 விளக்கம்:</b> {r.get('kural_explanation')}</div>
                            </div>""", unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="result-box box-solution">
                                <span class="box-header label-solution">✅ வள்ளுவர் தீர்வு:</span>
                                <div class="box-text">{r.get('solution')}</div>
                            </div>""", unsafe_allow_html=True)
                            
                            st.markdown(f"""
                            <div class="result-box box-consequence">
                                <span class="box-header label-consequence">⚠️ இதை மீறினால்:</span>
                                <div class="box-text">{r.get('consequence')}</div>
                            </div>""", unsafe_allow_html=True)
                    else:
                        with st.chat_message("assistant"):
                            st.write(text_resp)

                except Exception as e:
                    st.error(f"பிழை: {e}")

# --- FOOTER ---
st.markdown("""
    <div class="footer">
        <p>© All rights reserved by <span style="font-weight:900; color:black;">MIN E KAVI (மின் கவி)</span></p>
        <p>Developed & Designed by <span style="font-weight:900; color:black;">VIGNESH M</span> | FOUNDER OF MIN E KAVI</p>
    </div>
""", unsafe_allow_html=True)