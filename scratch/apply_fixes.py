import re
import os

app_path = r"c:\Users\SHREYAS\Desktop\MediScan-AI-main\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Add 'import os' if not present
if "import os\n" not in code and "import os," not in code:
    code = code.replace("import streamlit as st\n", "import streamlit as st\nimport os\n", 1)

# 2. Update client initialization and add fallback helpers
old_client_block = """# ── Google Gemini Client (PRIMARY REASONING ENGINE) ─────────────────────────
# Architecture: Gemini handles ALL text generation (triage, health coach) and
# multimodal vision analysis. This is the core intelligence layer of MediScan AI.
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    _api_ready = True
except Exception as exc:
    client = None
    _api_ready = False
    logger.warning("Gemini client init failed: %s", exc)

# ── Groq Client (WHISPER STT ONLY) ────────────────────────────────────────────
# Architecture: Groq is used EXCLUSIVELY for Whisper-based speech-to-text
# transcription, leveraging its low-latency inference for real-time audio.
# All reasoning and generation tasks are handled by Gemini above.
try:
    groq_key = st.secrets.get("GROQ_API_KEY")
    groq_client = Groq(api_key=groq_key) if groq_key else None
except Exception as exc:
    groq_client = None
    logger.warning("Groq client init failed: %s", exc)

EMERGENCY_WEBHOOK_URL = "https://hook.us1.make.com/mock-emergency"
LANG_MAP = {"English": "en", "Hindi (हिन्दी)": "hi", "Marathi (मराठी)": "mr", "Bengali (বাংলা)": "bn", "Spanish (Español)": "es"}"""

new_client_block = """# ── API Key Resolution & Resilient Model Inference ────────────────────────────
def get_api_key(name: str) -> str:
    \"\"\"Multi-tiered credential resolution: session_state -> st.secrets -> os.environ.\"\"\"
    # 1. Custom key entered in UI
    custom_val = st.session_state.get(f"custom_{name}", "").strip()
    if custom_val:
        return custom_val
    # 2. Streamlit secrets (safely handled if secrets.toml is missing)
    try:
        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    # 3. Environment variables
    return os.environ.get(name, "").strip()


def init_gemini_client():
    key = get_api_key("GEMINI_API_KEY")
    if not key:
        return None
    try:
        return genai.Client(api_key=key)
    except Exception as exc:
        logger.warning("Gemini client init failed: %s", exc)
        return None


def init_groq_client():
    key = get_api_key("GROQ_API_KEY")
    if not key:
        return None
    try:
        return Groq(api_key=key)
    except Exception as exc:
        logger.warning("Groq client init failed: %s", exc)
        return None


# Primary candidate models with graceful degradation
GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
]

GROQ_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "mixtral-8x7b-32768",
]


def call_gemini_with_fallback(client, contents, system_instruction: str = None) -> tuple[str, str]:
    \"\"\"Execute Gemini generation with automatic candidate model fallback on 404/NotFound.\"\"\"
    last_err = None
    config = types.GenerateContentConfig(system_instruction=system_instruction) if system_instruction else None
    for model_name in GEMINI_MODELS:
        try:
            resp = client.models.generate_content(
                model=model_name,
                contents=contents,
                config=config,
            )
            return resp.text, model_name
        except Exception as exc:
            last_err = exc
            err_str = str(exc).lower()
            if "not found" in err_str or "404" in err_str:
                logger.info("Gemini model %s not available, attempting fallback: %s", model_name, exc)
                continue
            logger.warning("Gemini generation failed on %s: %s", model_name, exc)
            raise exc
    raise last_err or RuntimeError("No candidate Gemini models were available.")


def call_groq_second_opinion(groq_client, primary_analysis: str) -> str:
    \"\"\"Generate second opinion via Groq Llama 3 with fallback across supported models.\"\"\"
    last_err = None
    for model_name in GROQ_MODELS:
        try:
            res = groq_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a Senior Medical Synthesizer reviewing a clinical AI triage / report OCR output. "
                            "Provide a concise, objective second opinion, highlight any missed biomarkers or nuances, "
                            "and deliver a unified consensus recommendation. Include standard disclaimers."
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Primary Clinical Analysis to review:\\n{primary_analysis}",
                    },
                ],
            )
            return res.choices[0].message.content
        except Exception as exc:
            last_err = exc
            logger.info("Groq model %s failed, attempting fallback: %s", model_name, exc)
            continue
    raise last_err or RuntimeError("All candidate Groq models failed.")


# Initialize clients
client = init_gemini_client()
_api_ready = client is not None
groq_client = init_groq_client()

EMERGENCY_WEBHOOK_URL = os.environ.get("EMERGENCY_WEBHOOK_URL", "https://hook.us1.make.com/mock-emergency")
LANG_MAP = {"English": "en", "Hindi (हिन्दी)": "hi", "Marathi (मराठी)": "mr", "Bengali (বাংলা)": "bn", "Spanish (Español)": "es"}"""

if old_client_block in code:
    code = code.replace(old_client_block, new_client_block, 1)
    print("Replaced client block successfully")
else:
    print("WARNING: Client block not found exactly")

# 3. Update fire_emergency_webhook to use custom webhook URL if set and reduce timeout
old_webhook_func = """def fire_emergency_webhook(payload: dict) -> bool:
    \"\"\"POST an emergency alert payload to the configured webhook endpoint.

    Returns True on a successful (2xx) response, False otherwise. Failures are
    logged rather than silently swallowed, and the outcome is recorded in
    session_state so the UI can honestly reflect whether the alert actually
    went out (this app currently points at a mock endpoint — see the caption
    shown alongside SOS/emergency triggers in the UI).
    \"\"\"
    ok = False
    try:
        resp = requests.post(EMERGENCY_WEBHOOK_URL, json=payload, timeout=4)
        ok = resp.ok
        if not ok:
            logger.warning("Emergency webhook returned status %s: %s", resp.status_code, resp.text[:200])
    except requests.exceptions.RequestException as exc:
        logger.error("Emergency webhook request failed: %s", exc)
        ok = False

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "alert": payload.get("alert", "unknown"),
        "delivered": ok,
    }
    if "webhook_log" not in st.session_state:
        st.session_state.webhook_log = []
    st.session_state.webhook_log.append(log_entry)
    return ok"""

new_webhook_func = """def fire_emergency_webhook(payload: dict) -> bool:
    \"\"\"POST an emergency alert payload to the configured webhook endpoint.\"\"\"
    webhook_url = st.session_state.get("custom_webhook_url") or EMERGENCY_WEBHOOK_URL
    ok = False
    try:
        resp = requests.post(webhook_url, json=payload, timeout=2.5)
        ok = resp.ok
        if not ok:
            logger.warning("Emergency webhook returned status %s: %s", resp.status_code, resp.text[:200])
    except requests.exceptions.RequestException as exc:
        logger.error("Emergency webhook request failed: %s", exc)
        ok = False

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "alert": payload.get("alert", "unknown"),
        "delivered": ok,
    }
    if "webhook_log" not in st.session_state:
        st.session_state.webhook_log = []
    st.session_state.webhook_log.append(log_entry)
    return ok"""

if old_webhook_func in code:
    code = code.replace(old_webhook_func, new_webhook_func, 1)
    print("Replaced fire_emergency_webhook successfully")
else:
    print("WARNING: fire_emergency_webhook not found exactly")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Pass 1 written")
