import json

from google import genai
from google.genai import types
import streamlit as st 
from twilio.rest import Client as TwilioClient

from prompts import SYSTEM_PROMPT, WELCOME_MESSAGE_TEMPLATE, SUMMARY_REQUEST_PROMPT

MODEL_NAME = "gemini-3.8-flash"
st.set_page_config(page_title="Nutrisnap", page_icon="🥗")

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = st.secrets["TWILIO_WHATSAPP_FROM"]
TWILIO_CONTENT_SID = st.secrets["TWILIO_CONTENT_SID"]

#step 1: Set up the GenAI client
@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)

@st.cache_resource
def get_twilio_client():
    return TwilioClient(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
 
gemini_client = get_gemini_client()
twilio_client = get_twilio_client()

def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.write(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"])

def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])

def ask_gemini(parts):
    try:
        return st.session_state.chat.send_message(parts).text 
    except Exception as error:
        return f"Sorry, something went wrong: {error}"

def clean_whatsapp_text(text):
    if not text:
        return "No nutrition summary available."
    text = " ".join(text.split())   #collapse whitespace/newlines
    return text[:1500] + "..." if len(text) > 1500 else text 

def send_whatsapp(to_number, user_name, summary):
    # Content template expects {{1}} = name, {{2}} = summary
    try:
        content_variables = json.dumps (
            {"1": user_name, "2": clean_whatsapp_text(summary)}, ensure_ascii=False
        )
        message = twilio_client.messages.create (
            from_ = TWILIO_WHATSAPP_FROM,
            to = f"whatsapp:{to_number}",
            content_sid = TWILIO_CONTENT_SID,
            content_variables = content_variables,
        )
        return True, message.sid
    except Exception as error:
        return False, str(error)

#Gotcha to flag live: Streamlit re-executes the entire script top to bottom on every interaction. 
# If genai.Client(...) is created as a plain top-level variable, a brand-new client is built on every rerun and the previous one is garbage-collected - closing its connection. Any chat session created from that old client then fails with "Cannot send a request, as the client has been closed." Wrapping creation in @st.cache_resource builds the client once per session and reuses it, so every chat and every message shares the same live connection.

#step 2: Building the onboarding screen 
if "onboarded" not in st.session_state:         #if "onboarded" not in st.session_state is the standard Streamlit pattern for "show this only once per session".
    st.title("🥗 Nutrisnap")
    st.caption("Snap it. Track it. Text yourself the results.")
    with st.form("onboarding_form"):
        name = st.text_input("Your name")
        whatsapp_number = st.text_input(
            "WhatsApp number (with country code)",
            placeholder="+91XXXXXXXXXX",
            help="This is the number where you'll receive your meal summaries via WhatsApp.",
        )
        submitted = st.form_submit_button("Let's go 🚀")
    if submitted:
        if not name.strip() or not whatsapp_number.strip():
            st.warning("Please fill in both your name and WhatsApp number.")
        else:
            st.session_state.name = name.strip()
            st.session_state.whatsapp_number = whatsapp_number.strip()
            #Activate my Gemini chat session with the system prompt
            st.session_state.chat = gemini_client.chats.create(
                model=MODEL_NAME,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            st.session_state.messages = []
            st.session_state.onboarded = True
            st.rerun()
    st.stop()

# Submitting the form is where the actual Gemini chat session is born - gemini_client.chats.create(...) with 
# system_instruction=SYSTEM_PROMPT gives the conversation its memory and its personality, and it's stored in session state so every later message reuses the same conversation.

# st.rerun() forces Streamlit to immediately restart the script so it picks up onboarded = True and skips straight past the form next time.

# Step 3: Main chat interface 
header_col, button_col = st.columns([5, 2], vertical_alignment = "center")

with header_col:
    st.title("🥗 Nutrisnap")

with button_col:
    send_disabled = len(st.session_state.messages) <= 0 
    if st.button("📤Send to WhatsApp", disabled = send_disabled, use_container_width = True):
        with st.spinner("Summarizing your day..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            success, info = send_whatsapp(st.session_state.whatsapp_number, st.session_state.name, summary)
            if success:
                st.success("Sent! Check your WhatsApp 📲")
            else:
                st.error(f"Couldn't send that: {info}")

st.caption(f"Logged in as {st.session_state.name} - updates to go {st.session_state.whatsapp_number}")

if not st.session_state.messages:
    add_message("assistant", "text", WELCOME_MESSAGE_TEMPLATE.format(name = st.session_state.name))
else:
    for message in st.session_state.messages:
        render_message(message)

user_input = st.chat_input(
    "Ask question, or attach a photo of your meal",
    accept_file = True,
    file_type = ["jpg", "jpeg", "png"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text 
    parts = [] 

    if photo is not None:
        photo_bytes = photo.getvalue() 
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))
    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append("What is this meal? Give me the calories and macros.")
 
    with st.spinner("Crunching the numbers..."):
        answer = ask_gemini(parts)
    add_message("assistant", "text", answer)

