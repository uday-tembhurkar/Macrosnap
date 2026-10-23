# 🥗 Nutrisnap

Nutrisnap is an AI-powered nutrition tracker that lets you log your meals with a quick photo upload. Get instant caloric and macro breakdowns on a web dashboard and receive an automated daily summary sent straight to your WhatsApp!

## 🚀 Features
- **AI Visual Recognition:** Uses Google Gemini 3.8 Flash to automatically detect foods, estimate portion sizes, and calculate calories.
- **Persistent Chat Interface:** Interactive Streamlit dashboard to ask follow-up questions about your diet history.
- **WhatsApp Integration:** Dispatches clean notification summaries directly to your phone using the Twilio Messaging API.
- **Secure Onboarding:** A streamlined, session-safe onboarding flow for user registration.

## 🛠️ Tech Stack
- **Language:** Python 3.14+
- **Frontend/UI:** Streamlit
- **AI Engine:** Google GenAI SDK (`gemini-3.8-flash`)
- **Messaging Pipeline:** Twilio WhatsApp Business API

## 💻 Local Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com
   cd nutrisnap-chatbot
   ```

2. **Create and activate a virtual environment:**
   ```powershell
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Configure Environment Variables:**
   Create a `.env` file at the root of the project and add your API credentials:
   ```text
   GEMINI_API_KEY=your_gemini_key
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_WHATSAPP_FROM=whatsapp:+14155238886
   TWILIO_CONTENT_SID=your_template_sid
   ```

5. **Run the application:**
   ```powershell
   streamlit run app.py
   ```
