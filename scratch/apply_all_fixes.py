import os

app_path = r"c:\Users\SHREYAS\Desktop\MediScan-AI-main\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    text = f.read()

has_crlf = "\r\n" in text
content = text.replace("\r\n", "\n")

# 1. Replace generate_doctor_pdf
start_marker = 'def generate_doctor_pdf(patient_name, record, emergency_contact, language,'
end_marker = '    doc.build(story)\n    buf.seek(0)\n    return buf\n'

start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx) + len(end_marker)

if start_idx != -1 and end_idx != -1:
    pdf_new = '''def generate_doctor_pdf(patient_name, record, emergency_contact, language,
                         include_chat=True, include_reports=True, include_biometrics=True,
                         doctor_name="", referring_note=""):
    """Builds an in-memory PDF clinical handoff summary for a doctor. Returns BytesIO."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        topMargin=0.6 * inch, bottomMargin=0.6 * inch,
        leftMargin=0.6 * inch, rightMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=18, spaceAfter=4)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontSize=13, spaceBefore=14, spaceAfter=6, textColor=colors.HexColor("#1a4d7a"))
    small = ParagraphStyle("small", parent=styles["Normal"], fontSize=8, textColor=colors.gray)
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5, leading=13.5)
    tag = ParagraphStyle("tag", parent=styles["Normal"], fontSize=8.5, textColor=colors.HexColor("#b02a2a"))

    def esc(text):
        if not text:
            return ""
        s = str(text)
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return s

    story = []

    story.append(Paragraph("🩺 MediScan AI — Clinical Handoff Summary", h1))
    story.append(Paragraph(
        f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} · Response language on record: {language}",
        small,
    ))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#1a4d7a"), thickness=1, spaceAfter=8))

    if doctor_name or referring_note:
        story.append(Paragraph(f"<b>Addressed to:</b> {esc(doctor_name) or 'Attending Physician'}", body))
        if referring_note:
            story.append(Paragraph(f"<b>Note from patient/carer:</b> {esc(referring_note)}", body))
        story.append(Spacer(1, 6))

    # ── Patient Profile ────────────────────────────────────────────────────
    story.append(Paragraph("Patient Profile", h2))
    prof = record.get("profile", {})
    profile_table_data = [
        [Paragraph("<b>Name</b>", body), Paragraph(esc(patient_name), body)],
        [Paragraph("<b>Age</b>", body), Paragraph(esc(prof.get("age", "—")), body)],
        [Paragraph("<b>Sex</b>", body), Paragraph(esc(prof.get("sex", "—")), body)],
        [Paragraph("<b>Weight</b>", body), Paragraph(f"{prof.get('weight_kg', 0):.1f} kg" if prof.get("weight_kg") else "—", body)],
        [Paragraph("<b>Chronic Conditions</b>", body), Paragraph(esc(prof.get("chronic_conditions") or "None reported"), body)],
    ]
    if emergency_contact and emergency_contact.get("name"):
        profile_table_data.append([
            Paragraph("<b>Emergency Contact</b>", body),
            Paragraph(f"{esc(emergency_contact['name'])} — {esc(emergency_contact.get('phone', ''))}", body)
        ])
    pt = Table(profile_table_data, colWidths=[1.8 * inch, 4.4 * inch])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f8")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(pt)

    # ── Structured Intake (most recent) ────────────────────────────────────
    intake = record.get("last_intake")
    if intake and intake.get("locked"):
        story.append(Paragraph("Most Recent Structured Intake", h2))
        intake_data = [
            [Paragraph("<b>Severity</b>", body), Paragraph(f"{intake.get('severity', '—')}/10", body)],
            [Paragraph("<b>Duration</b>", body), Paragraph(esc(intake.get("duration", "—")), body)],
            [Paragraph("<b>Onset</b>", body), Paragraph(esc(intake.get("onset", "—")), body)],
            [Paragraph("<b>Affected Area(s)</b>", body), Paragraph(esc(", ".join(intake.get("body_areas", [])) or "Not specified"), body)],
        ]
        it = Table(intake_data, colWidths=[1.8 * inch, 4.4 * inch])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f8")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(it)

    # ── Biometric Trend ─────────────────────────────────────────────────────
    if include_biometrics and not record["health_metrics"].empty:
        story.append(Paragraph("6-Month Biometric Trend", h2))
        hm = record["health_metrics"]
        header = ["Month", "Resting HR", "Systolic BP", "Fasting Glucose", "Risk Score"]
        rows = [header] + hm[["Month", "Resting_HR", "Systolic_BP", "Fasting_Glucose", "Health_Risk_Score"]].astype(str).values.tolist()
        bt = Table(rows, colWidths=[1.2 * inch] * 5)
        bt.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a4d7a")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
            ("ALIGN", (1, 0), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f8fb")]),
        ]))
        story.append(bt)
        latest = hm.iloc[-1]
        flag_label, _ = metric_flag("Health_Risk_Score", float(latest["Health_Risk_Score"]))
        story.append(Paragraph(f"Latest Health Risk Score: <b>{int(float(latest['Health_Risk_Score']))}/100</b> ({esc(flag_label)})", body))

    # ── AI Triage Transcript ────────────────────────────────────────────────
    if include_chat and record["chat_history"]:
        story.append(Paragraph("AI Triage Session Transcript", h2))
        story.append(Paragraph(
            "The following is an automated triage conversation between the patient and MediScan AI. "
            "This is provided for context only and does not constitute a clinical diagnosis.", tag,
        ))
        story.append(Spacer(1, 4))
        for m in record["chat_history"]:
            role_label = "Patient" if m["role"] == "user" else "MediScan AI"
            content = m["content"]
            # Strip internal JSON block from PDF view
            content = re.sub(r'```json\s*\{.*?\}\s*```', '', content, flags=re.DOTALL)
            text = esc(content).replace("\n", "<br/>")
            story.append(Paragraph(f"<b>{role_label}:</b> {text}", body))
            story.append(Spacer(1, 6))

    # ── Report / Lab Analysis History ──────────────────────────────────────
    if include_reports and record["report_history"]:
        story.append(PageBreak())
        story.append(Paragraph("Lab / Visual Report Analyses", h2))
        for r in record["report_history"]:
            story.append(Paragraph(f"<b>{esc(r['filename'])}</b> — {esc(r['timestamp'])}", body))
            text = esc(r["result"]).replace("\n", "<br/>")
            story.append(Paragraph(text, body))
            if r.get("second_opinion"):
                story.append(Spacer(1, 4))
                so_text = esc(r["second_opinion"]).replace("\n", "<br/>")
                story.append(Paragraph(f"<b>⚖️ Senior Medical Synthesizer Consensus (Groq Llama 3):</b><br/>{so_text}", body))
            story.append(Spacer(1, 10))

    # ── Doctor Notes Section ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("Physician Notes", h2))
    story.append(Paragraph("(Space reserved for clinician annotations, diagnosis, and treatment plan.)", small))
    story.append(Spacer(1, 10))
    for _ in range(10):
        story.append(HRFlowable(width="100%", color=colors.HexColor("#cccccc"), thickness=0.5, spaceAfter=18))

    story.append(Spacer(1, 20))
    story.append(Paragraph(
        "***CDSCO COMPLIANCE DISCLAIMER:*** MediScan AI is a Clinical Decision Support System (CDSS). "
        "The information in this document is generated by an artificial intelligence model and is strictly "
        "for triage and informational purposes. It is NOT a substitute for professional medical advice, "
        "diagnosis, or treatment. This summary is intended to assist — not replace — clinical judgment.",
        ParagraphStyle("disclaimer", parent=styles["Normal"], fontSize=8, textColor=colors.gray, spaceBefore=10),
    ))

    doc.build(story)
    buf.seek(0)
    return buf\n'''
    content = content[:start_idx] + pdf_new + content[end_idx:]
    print("Replaced generate_doctor_pdf successfully")
else:
    print("WARNING: start or end marker not found for generate_doctor_pdf")

# 2. Update Tab 1 Structured Intake Form
old_tab1_intake = """    with st.expander("📋 Structured Intake (optional, improves accuracy)"):
        with st.form("structured_intake_form", clear_on_submit=False):
            ci1, ci2, ci3 = st.columns(3)
            severity = ci1.slider("Severity (1 = mild, 10 = severe)", 1, 10, 5, key="intake_severity")
            duration = ci2.selectbox("Duration", ["< 1 day", "1-3 days", "4-7 days", "1-4 weeks", "> 1 month"], key="intake_duration")
            onset = ci3.selectbox("Onset", ["Sudden", "Gradual", "Not sure"], key="intake_onset")
            body_areas = st.multiselect(
                "Affected Body Area(s)",
                ["Head", "Chest", "Abdomen", "Back", "Arms", "Legs", "Skin", "Throat", "Eyes", "Whole body", "Other"],
                key="intake_areas",
            )
            st.form_submit_button("✅ Lock Intake", use_container_width=True)"""

new_tab1_intake = """    current_intake = active_record.get("last_intake") or {}
    intake_locked = bool(current_intake.get("locked"))
    with st.expander("📋 Structured Intake (optional, improves accuracy)", expanded=intake_locked):
        if intake_locked:
            st.success(
                f"🔒 **Intake Active & Locked:** Severity: {current_intake.get('severity')}/10 | "
                f"Duration: {current_intake.get('duration')} | Onset: {current_intake.get('onset')} | "
                f"Areas: {', '.join(current_intake.get('body_areas', [])) or 'None'}"
            )
            if st.button("🔓 Unlock / Reset Intake", key="unlock_intake_btn", use_container_width=True):
                active_record["last_intake"] = None
                st.rerun()
        else:
            with st.form("structured_intake_form", clear_on_submit=False):
                st.caption("Provide additional clinical context to assist triage ranking. If left unlocked, symptoms are evaluated naturally.")
                ci1, ci2, ci3 = st.columns(3)
                severity = ci1.slider("Severity (1 = mild, 10 = severe)", 1, 10, int(current_intake.get("severity") or 5), key="intake_severity")
                duration = ci2.selectbox("Duration", ["< 1 day", "1-3 days", "4-7 days", "1-4 weeks", "> 1 month"],
                                         index=["< 1 day", "1-3 days", "4-7 days", "1-4 weeks", "> 1 month"].index(current_intake.get("duration", "1-3 days")),
                                         key="intake_duration")
                onset = ci3.selectbox("Onset", ["Sudden", "Gradual", "Not sure"],
                                      index=["Sudden", "Gradual", "Not sure"].index(current_intake.get("onset", "Gradual")),
                                      key="intake_onset")
                body_areas = st.multiselect(
                    "Affected Body Area(s)",
                    ["Head", "Chest", "Abdomen", "Back", "Arms", "Legs", "Skin", "Throat", "Eyes", "Whole body", "Other"],
                    default=current_intake.get("body_areas", []),
                    key="intake_areas",
                )
                if st.form_submit_button("✅ Lock Intake for Current Session", use_container_width=True, type="primary"):
                    active_record["last_intake"] = {
                        "severity": severity, "duration": duration, "onset": onset, "body_areas": body_areas, "locked": True
                    }
                    st.success("✅ Structured intake locked! It will be factored into your next triage inquiry.")
                    st.rerun()"""

if old_tab1_intake in content:
    content = content.replace(old_tab1_intake, new_tab1_intake, 1)
    print("Replaced Tab 1 intake successfully")
else:
    print("WARNING: Tab 1 intake not found")

# 3. Update Chat History Rendering
old_chat_render = """    # ── Render Chat History with feedback controls ────────────────────────────
    for idx, message in enumerate(active_record["chat_history"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                fb_col1, fb_col2, _ = st.columns([1, 1, 8])
                current_fb = active_record["feedback"].get(idx)
                if fb_col1.button("👍", key=f"fb_up_{idx}", type="primary" if current_fb == "up" else "secondary"):
                    active_record["feedback"][idx] = "up"
                    st.rerun()
                if fb_col2.button("👎", key=f"fb_down_{idx}", type="primary" if current_fb == "down" else "secondary"):
                    active_record["feedback"][idx] = "down"
                    st.rerun()"""

new_chat_render = """    # ── Render Chat History with feedback & voice controls ───────────────────
    for idx, message in enumerate(active_record["chat_history"]):
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                fb_c1, fb_c2, fb_c3, _ = st.columns([1, 1, 4, 4])
                current_fb = active_record["feedback"].get(idx)
                if fb_c1.button("👍", key=f"fb_up_{idx}", type="primary" if current_fb == "up" else "secondary"):
                    active_record["feedback"][idx] = None if current_fb == "up" else "up"
                    st.rerun()
                if fb_c2.button("👎", key=f"fb_down_{idx}", type="primary" if current_fb == "down" else "secondary"):
                    active_record["feedback"][idx] = None if current_fb == "down" else "down"
                    st.rerun()
                if message.get("audio"):
                    fb_c3.audio(message["audio"], format="audio/mp3")
                else:
                    if fb_c3.button("🔊 Read Aloud", key=f"tts_btn_{idx}"):
                        try:
                            c_txt = re.sub(r'```.*?```', '', message["content"], flags=re.DOTALL)
                            c_txt = c_txt.replace("*", "").replace("#", "").strip()
                            t_lang = LANG_MAP.get(st.session_state.app_language, "en")
                            tts = gTTS(text=c_txt[:600], lang=t_lang, slow=False)
                            a_buf = io.BytesIO()
                            tts.write_to_fp(a_buf)
                            message["audio"] = a_buf.getvalue()
                            st.rerun()
                        except Exception as tts_err:
                            fb_c3.caption(f"Audio error: {tts_err}")"""

if old_chat_render in content:
    content = content.replace(old_chat_render, new_chat_render, 1)
    print("Replaced chat rendering successfully")
else:
    print("WARNING: chat rendering not found")

# 4. Update Tab 1 Inference & Audio
old_triage_inference = """    if user_text or is_new_audio:
        profile = active_record["profile"]

        active_record["last_intake"] = {
            "severity": severity, "duration": duration, "onset": onset, "body_areas": body_areas,
        }

        intake_summary = (
            f"\\nSTRUCTURED INTAKE:\\n- Severity: {severity}/10\\n- Duration: {duration}\\n"
            f"- Onset: {onset}\\n- Affected area(s): {', '.join(body_areas) if body_areas else 'Not specified'}\\n"
        )

        dynamic_system_instruction = f\"\"\"{TRIAGE_SYSTEM_INSTRUCTION}

PATIENT BIOMETRIC BASELINE:
- Age: {profile.get('age', 'Not provided')} years
- Sex: {profile.get('sex', 'Not provided')}
- Weight: {profile.get('weight_kg', 'Not provided')} kg
- Chronic Conditions: {profile.get('chronic_conditions') or 'None reported'}
{intake_summary}
CRITICAL LANGUAGE INSTRUCTION:
You must translate your entire response, including the differential diagnosis and recommended steps, into {st.session_state.app_language}. Ensure medical terms are accurately translated or transliterated. The CDSCO disclaimer must also be translated into {st.session_state.app_language}.
\"\"\"

        final_symptom_text = user_text or ""

        if is_new_audio and audio_value is not None and groq_client is not None:
            with st.spinner("🎙️ Transcribing audio with Groq Whisper..."):
                try:
                    transcription = groq_client.audio.transcriptions.create(
                        file=("audio.wav", audio_value.read()), model="whisper-large-v3-turbo"
                    )
                    final_symptom_text = f"{final_symptom_text}\\nVoice note: {transcription.text}".strip()
                except Exception as exc:
                    logger.error("Whisper transcription failed: %s", exc)
                    st.error(f"🎙️ Whisper transcription error: {exc}")

        if final_symptom_text.strip():
            with st.chat_message("user"):
                st.markdown(final_symptom_text)
            active_record["chat_history"].append({"role": "user", "content": final_symptom_text})

            # Build conversation context for Gemini (single-turn with history)
            conversation_context = ""
            for msg in active_record["chat_history"]:
                role_label = "Patient" if msg["role"] == "user" else "MediScan AI"
                conversation_context += f"{role_label}: {msg['content']}\\n\\n"

            # Programmatic prompt deduplication / cache lookup to prevent redundant Gemini API calls on duplicate submissions
            prompt_cache_key = hashlib.md5(
                f"{st.session_state.active_patient}_{final_symptom_text}_{st.session_state.app_language}_{intake_summary}".encode()
            ).hexdigest()

            assistant_reply = None
            if prompt_cache_key in st.session_state.triage_prompt_cache:
                logger.info("Serving cached triage response for prompt key %s", prompt_cache_key)
                assistant_reply = st.session_state.triage_prompt_cache[prompt_cache_key]
                with st.chat_message("assistant"):
                    st.caption("⚡ *Loaded from session cache*")
                    st.markdown(assistant_reply)
            else:
                with st.chat_message("assistant"):
                    with st.spinner(f"🧠 Analysing symptoms in {st.session_state.app_language}..."):
                        try:
                            response = client.models.generate_content(
                                model="gemini-3.6-flash",
                                contents=conversation_context,
                                config=types.GenerateContentConfig(system_instruction=dynamic_system_instruction),
                            )
                            assistant_reply = response.text
                            st.session_state.triage_prompt_cache[prompt_cache_key] = assistant_reply
                        except Exception as exc:
                            logger.error("Gemini triage call failed: %s", exc)
                            assistant_reply = f"⚠️ **Error communicating with Gemini:** `{exc}`"
                    st.markdown(assistant_reply)

                # ── Programmatic urgency detection via structured JSON output ──
                is_critical = False
                try:
                    json_match = re.search(r'\\{[^{}]*"urgency_level"[^{}]*\\}', assistant_reply)
                    if json_match:
                        urgency_data = json.loads(json_match.group())
                        if urgency_data.get("urgency_level") in ("High", "Emergency"):
                            is_critical = True
                except (json.JSONDecodeError, AttributeError) as exc:
                    logger.info("Urgency JSON parse fell back to keyword scan: %s", exc)
                if not is_critical:
                    # Fallback: keyword-based detection if JSON parsing failed
                    critical_keywords = ["urgent care", "emergency", "immediate", "hospital", "chest pain", "stroke"]
                    is_critical = any(kw in assistant_reply.lower() for kw in critical_keywords)
                if is_critical:
                    delivered = fire_emergency_webhook({
                        "alert": "critical_symptoms",
                        "patient": st.session_state.active_patient,
                        "profile": profile,
                        "emergency_contact": st.session_state.emergency_contact,
                        "timestamp": datetime.now().isoformat(),
                    })
                    if delivered:
                        st.error(
                            "🚨 **CRITICAL TRIAGE ESCALATION** 🚨\\n\\nHigh-risk symptoms detected. "
                            f"Notifying {st.session_state.emergency_contact.get('name') or 'emergency dispatch'}."
                        )
                    else:
                        st.error(
                            "🚨 **CRITICAL TRIAGE ESCALATION** 🚨\\n\\nHigh-risk symptoms detected, but the "
                            "alert endpoint did not confirm delivery (this is a mock webhook in the prototype). "
                            "Please seek in-person or emergency care directly."
                        )

                tts_lang = LANG_MAP.get(st.session_state.app_language, "en")
                try:
                    clean_text = assistant_reply.replace("*", "").replace("#", "")
                    tts = gTTS(text=clean_text, lang=tts_lang, slow=False)
                    audio_fp = io.BytesIO()
                    tts.write_to_fp(audio_fp)
                    audio_fp.seek(0)
                    st.audio(audio_fp, format="audio/mp3")
                except Exception as exc:
                    logger.warning("gTTS synthesis failed: %s", exc)
                    st.caption("🔇 Audio synthesis is temporarily unavailable.")

            active_record["chat_history"].append({"role": "assistant", "content": assistant_reply})

        if audio_hash:
            active_record["last_processed_audio_hash"] = audio_hash
        st.rerun()"""

new_triage_inference = """    if user_text or is_new_audio:
        profile = active_record["profile"]

        # Only inject structured intake if the user explicitly submitted / locked it
        cur_intake = active_record.get("last_intake")
        if cur_intake and cur_intake.get("locked"):
            intake_summary = (
                f"\\nSTRUCTURED INTAKE:\\n- Severity: {cur_intake.get('severity')}/10\\n- Duration: {cur_intake.get('duration')}\\n"
                f"- Onset: {cur_intake.get('onset')}\\n- Affected area(s): {', '.join(cur_intake.get('body_areas', [])) or 'Not specified'}\\n"
            )
        else:
            intake_summary = ""

        dynamic_system_instruction = f\"\"\"{TRIAGE_SYSTEM_INSTRUCTION}

PATIENT BIOMETRIC BASELINE:
- Age: {profile.get('age', 'Not provided')} years
- Sex: {profile.get('sex', 'Not provided')}
- Weight: {profile.get('weight_kg', 'Not provided')} kg
- Chronic Conditions: {profile.get('chronic_conditions') or 'None reported'}
{intake_summary}
CRITICAL LANGUAGE INSTRUCTION:
You must translate your entire response, including the differential diagnosis and recommended steps, into {st.session_state.app_language}. Ensure medical terms are accurately translated or transliterated. The CDSCO disclaimer must also be translated into {st.session_state.app_language}.
\"\"\"

        final_symptom_text = user_text or ""

        if is_new_audio and audio_value is not None and groq_client is not None:
            with st.spinner("🎙️ Transcribing audio with Groq Whisper..."):
                try:
                    transcription = groq_client.audio.transcriptions.create(
                        file=("audio.wav", io.BytesIO(audio_bytes)),
                        model="whisper-large-v3-turbo",
                    )
                    final_symptom_text = f"{final_symptom_text}\\nVoice note: {transcription.text}".strip()
                except Exception as exc:
                    logger.error("Whisper transcription failed: %s", exc)
                    st.error(f"🎙️ Whisper transcription error: {exc}")

        if final_symptom_text.strip():
            with st.chat_message("user"):
                st.markdown(final_symptom_text)
            active_record["chat_history"].append({"role": "user", "content": final_symptom_text})

            # Build conversation context for Gemini (single-turn with history)
            conversation_context = ""
            for msg in active_record["chat_history"]:
                role_label = "Patient" if msg["role"] == "user" else "MediScan AI"
                conversation_context += f"{role_label}: {msg['content']}\\n\\n"

            prompt_cache_key = hashlib.md5(
                f"{st.session_state.active_patient}_{final_symptom_text}_{st.session_state.app_language}_{intake_summary}".encode()
            ).hexdigest()

            assistant_reply = None
            audio_bytes_generated = None
            if prompt_cache_key in st.session_state.triage_prompt_cache:
                logger.info("Serving cached triage response for prompt key %s", prompt_cache_key)
                assistant_reply = st.session_state.triage_prompt_cache[prompt_cache_key]
            else:
                with st.chat_message("assistant"):
                    with st.spinner(f"🧠 Analysing symptoms in {st.session_state.app_language}..."):
                        try:
                            assistant_reply, used_model = call_gemini_with_fallback(
                                client=client,
                                contents=conversation_context,
                                system_instruction=dynamic_system_instruction,
                            )
                            st.session_state.triage_prompt_cache[prompt_cache_key] = assistant_reply
                        except Exception as exc:
                            logger.error("Gemini triage call failed: %s", exc)
                            assistant_reply = f"⚠️ **Error communicating with Gemini:** `{exc}`"

                # Programmatic urgency detection
                is_critical = False
                try:
                    json_match = re.search(r'\\{[^{}]*"urgency_level"[^{}]*\\}', assistant_reply)
                    if json_match:
                        urgency_data = json.loads(json_match.group())
                        if urgency_data.get("urgency_level") in ("High", "Emergency"):
                            is_critical = True
                except (json.JSONDecodeError, AttributeError) as exc:
                    logger.info("Urgency JSON parse fell back to keyword scan: %s", exc)
                if not is_critical:
                    critical_keywords = ["urgent care", "emergency", "immediate", "hospital", "chest pain", "stroke"]
                    is_critical = any(kw in assistant_reply.lower() for kw in critical_keywords)
                if is_critical:
                    delivered = fire_emergency_webhook({
                        "alert": "critical_symptoms",
                        "patient": st.session_state.active_patient,
                        "profile": profile,
                        "emergency_contact": st.session_state.emergency_contact,
                        "timestamp": datetime.now().isoformat(),
                    })
                    if delivered:
                        st.error(
                            "🚨 **CRITICAL TRIAGE ESCALATION** 🚨\\n\\nHigh-risk symptoms detected. "
                            f"Notifying {st.session_state.emergency_contact.get('name') or 'emergency dispatch'}."
                        )
                    else:
                        st.error(
                            "🚨 **CRITICAL TRIAGE ESCALATION** 🚨\\n\\nHigh-risk symptoms detected, but the "
                            "alert endpoint did not confirm delivery. Please seek in-person emergency care directly."
                        )

                # Synthesize TTS audio to store permanently in message
                tts_lang = LANG_MAP.get(st.session_state.app_language, "en")
                try:
                    clean_text = re.sub(r'```.*?```', '', assistant_reply, flags=re.DOTALL)
                    clean_text = clean_text.replace("*", "").replace("#", "").strip()
                    if clean_text:
                        tts = gTTS(text=clean_text[:600], lang=tts_lang, slow=False)
                        audio_fp = io.BytesIO()
                        tts.write_to_fp(audio_fp)
                        audio_bytes_generated = audio_fp.getvalue()
                except Exception as exc:
                    logger.warning("gTTS synthesis failed: %s", exc)

            active_record["chat_history"].append({
                "role": "assistant",
                "content": assistant_reply,
                "audio": audio_bytes_generated,
            })

        if audio_hash:
            active_record["last_processed_audio_hash"] = audio_hash
        st.rerun()"""

if old_triage_inference in content:
    content = content.replace(old_triage_inference, new_triage_inference, 1)
    print("Replaced triage inference block successfully")
else:
    print("WARNING: triage inference block not found")

# 5. Update Tab 2 Vision Analysis & Second Opinion
old_tab2_block = """            for fname, fobj in image_sources:
                with st.spinner(f"Analyzing {fname} in {st.session_state.app_language}..."):
                    try:
                        pil_image = Image.open(fobj)
                        response = client.models.generate_content(
                            model="gemini-3.6-flash",
                            contents=[context_text, "Please analyze this medical image.", pil_image],
                            config=types.GenerateContentConfig(system_instruction=lang_vision_instruction),
                        )
                        result_text = response.text
                    except Exception as exc:
                        logger.error("Gemini vision analysis failed for %s: %s", fname, exc)
                        result_text = f"⚠️ **Gemini API error:** `{exc}`"
                    active_record["report_history"].append({
                        "id": uuid.uuid4().hex,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "filename": fname,
                        "result": result_text,
                    })
            st.rerun()

    if active_record["report_history"]:
        st.markdown("---")
        st.markdown(f"### 🗂️ Report History ({len(active_record['report_history'])})")
        for i, r in enumerate(reversed(active_record["report_history"])):
            # Deletion/second-opinion actions reference the report by its stable
            # uuid (assigned at creation) rather than by list position, so a
            # click can never land on the wrong entry even if the underlying
            # list is mutated between renders.
            report_id = r.get("id") or uuid.uuid4().hex
            with st.expander(f"👁️ {r['filename']} — {r['timestamp']}", expanded=(i == 0)):
                st.markdown(r["result"])
                bc1, bc2 = st.columns(2)
                if bc1.button("⚖️ Second Opinion (Groq Llama 3)", key=f"second_opinion_{report_id}",
                              use_container_width=True, disabled=groq_client is None):
                    with st.spinner("Consulting Groq Llama 3 Synthesizer..."):
                        try:
                            second_opinion = groq_client.chat.completions.create(
                                model="openai/gpt-oss-20b",
                                messages=[
                                    {"role": "system", "content": "You are a Senior Medical Synthesizer. Review the primary AI's OCR report analysis. Provide a brief second opinion, highlight any missed nuances, and give a final unified consensus."},
                                    {"role": "user", "content": f"Primary Analysis:\\n{r['result']}"},
                                ],
                            )
                            st.info(second_opinion.choices[0].message.content, icon="🤖")
                        except Exception as exc:
                            logger.error("Groq second-opinion call failed: %s", exc)
                            st.error(f"Error generating second opinion: {exc}")
                if bc2.button("🗑️ Delete This Report", key=f"delete_report_{report_id}", use_container_width=True):
                    active_record["report_history"] = [
                        item for item in active_record["report_history"]
                        if item.get("id") != report_id
                    ]
                    st.rerun()"""

new_tab2_block = """            for fname, fobj in image_sources:
                with st.spinner(f"Analyzing {fname} in {st.session_state.app_language}..."):
                    try:
                        pil_image = Image.open(fobj)
                        result_text, used_model = call_gemini_with_fallback(
                            client=client,
                            contents=[context_text, "Please analyze this medical image.", pil_image],
                            system_instruction=lang_vision_instruction,
                        )
                    except Exception as exc:
                        logger.error("Gemini vision analysis failed for %s: %s", fname, exc)
                        result_text = f"⚠️ **Gemini API error:** `{exc}`"
                    active_record["report_history"].append({
                        "id": uuid.uuid4().hex,
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "filename": fname,
                        "result": result_text,
                        "second_opinion": None,
                    })
            st.rerun()

    if active_record["report_history"]:
        st.markdown("---")
        st.markdown(f"### 🗂️ Report History ({len(active_record['report_history'])})")
        for i, r in enumerate(reversed(active_record["report_history"])):
            report_id = r.get("id") or uuid.uuid4().hex
            with st.expander(f"👁️ {r['filename']} — {r['timestamp']}", expanded=(i == 0)):
                st.markdown(r["result"])
                if r.get("second_opinion"):
                    st.markdown("---")
                    st.markdown(f"**⚖️ Senior Medical Synthesizer Consensus (Groq Llama 3 — {r.get('second_opinion_ts', '')})**")
                    st.info(r["second_opinion"], icon="🤖")

                bc1, bc2 = st.columns(2)
                if bc1.button("⚖️ Second Opinion (Groq Llama 3)", key=f"second_opinion_{report_id}",
                              use_container_width=True, disabled=groq_client is None):
                    with st.spinner("Consulting Groq Llama 3 Synthesizer..."):
                        try:
                            so_text = call_groq_second_opinion(groq_client, r["result"])
                            r["second_opinion"] = so_text
                            r["second_opinion_ts"] = datetime.now().strftime("%Y-%m-%d %H:%M")
                            st.success("✅ Senior second opinion consensus saved!")
                            st.rerun()
                        except Exception as exc:
                            logger.error("Groq second-opinion call failed: %s", exc)
                            st.error(f"Error generating second opinion: {exc}")
                if bc2.button("🗑️ Delete This Report", key=f"delete_report_{report_id}", use_container_width=True):
                    active_record["report_history"] = [
                        item for item in active_record["report_history"]
                        if item.get("id") != report_id
                    ]
                    st.rerun()"""

if old_tab2_block in content:
    content = content.replace(old_tab2_block, new_tab2_block, 1)
    print("Replaced Tab 2 vision & second opinion successfully")
else:
    print("WARNING: Tab 2 block not found")

# 6. Update Tab 3 KPI metrics and Live Telemetry alert cooldown
old_tab3_kpi = """    # ── KPI Summary Row ──────────────────────────────────────────────────────────
    kpi1, kpi2, kpi3 = st.columns(3)
    _latest_risk = active_record["health_metrics"].iloc[-1]["Health_Risk_Score"]
    _prev_risk = active_record["health_metrics"].iloc[-2]["Health_Risk_Score"]
    kpi1.metric("📊 Overall Risk Trend", f"{int(_latest_risk)} / 100",
                delta=int(_latest_risk - _prev_risk), delta_color="inverse")"""

new_tab3_kpi = """    # ── KPI Summary Row ──────────────────────────────────────────────────────────
    kpi1, kpi2, kpi3 = st.columns(3)
    hm_kpi = active_record["health_metrics"]
    if len(hm_kpi) >= 2:
        _latest_risk = float(hm_kpi.iloc[-1].get("Health_Risk_Score", 0) or 0)
        _prev_risk = float(hm_kpi.iloc[-2].get("Health_Risk_Score", 0) or 0)
        kpi1.metric("📊 Overall Risk Trend", f"{int(_latest_risk)} / 100",
                    delta=int(_latest_risk - _prev_risk), delta_color="inverse")
    elif len(hm_kpi) == 1:
        _latest_risk = float(hm_kpi.iloc[-1].get("Health_Risk_Score", 0) or 0)
        kpi1.metric("📊 Overall Risk Trend", f"{int(_latest_risk)} / 100")
    else:
        kpi1.metric("📊 Overall Risk Trend", "No records")"""

if old_tab3_kpi in content:
    content = content.replace(old_tab3_kpi, new_tab3_kpi, 1)
    print("Replaced Tab 3 KPI row successfully")
else:
    print("WARNING: Tab 3 KPI row not found")

# 7. Update Telemetry SpO2 Alert Cooldown
old_spo2_alert = """        if current_spo2 < 92:
            delivered = fire_emergency_webhook({"alert": "low_spo2", "value": int(current_spo2), "patient": st.session_state.active_patient})
            st.error(
                "🚨 **CRITICAL: SpO2 DROP DETECTED (simulated demo data)** 🚨\\n\\n"
                f"Simulated blood oxygen has fallen below 92%. {'Webhook notified.' if delivered else 'Webhook did not confirm delivery.'}"
            )"""

new_spo2_alert = """        if current_spo2 < 92:
            last_alert_ts = st.session_state.get("_last_spo2_alert_ts", 0)
            now_ts = time.time()
            if now_ts - last_alert_ts > 60:
                st.session_state._last_spo2_alert_ts = now_ts
                delivered = fire_emergency_webhook({"alert": "low_spo2", "value": int(current_spo2), "patient": st.session_state.active_patient})
                st.error(
                    "🚨 **CRITICAL: SpO2 DROP DETECTED (simulated demo data)** 🚨\\n\\n"
                    f"Simulated blood oxygen has fallen below 92%. {'Webhook notified.' if delivered else 'Webhook did not confirm delivery.'}"
                )"""

if old_spo2_alert in content:
    content = content.replace(old_spo2_alert, new_spo2_alert, 1)
    print("Replaced SpO2 alert cooldown successfully")
else:
    print("WARNING: SpO2 alert cooldown not found")

# 8. Update Biometric Editor Latest Readings & Health Coach
old_latest_readings = """    st.divider()
    st.markdown("### 📍 Latest Readings")
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    col1, col2, col3 = st.columns(3)
    for col, field, label, icon in [
        (col1, "Health_Risk_Score", "Health Risk Score", "⚠️"),
        (col2, "Resting_HR", "Resting HR", "💓"),
        (col3, "Fasting_Glucose", "Fasting Glucose", "🩸"),
    ]:
        flag_label, flag_color = metric_flag(field, latest[field])
        col.metric(
            label=f"{icon} {label}", value=f"{int(latest[field])}",
            delta=int(latest[field] - prev[field]), delta_color="inverse",
        )
        col.markdown(f":{flag_color}[{flag_label}]")

    if latest["Health_Risk_Score"] >= 85:
        delivered = fire_emergency_webhook({"alert": "high_risk_score", "score": int(latest["Health_Risk_Score"]), "patient": st.session_state.active_patient})
        st.error(
            "🚨 **CRITICAL RISK THRESHOLD EXCEEDED** 🚨\\n\\nScore is >= 85. "
            f"{'Preventative webhook notified.' if delivered else 'Webhook did not confirm delivery.'}"
        )"""

new_latest_readings = """    st.divider()
    st.markdown("### 📍 Latest Readings")
    if not df.empty:
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) >= 2 else latest

        col1, col2, col3 = st.columns(3)
        for col, field, label, icon in [
            (col1, "Health_Risk_Score", "Health Risk Score", "⚠️"),
            (col2, "Resting_HR", "Resting HR", "💓"),
            (col3, "Fasting_Glucose", "Fasting Glucose", "🩸"),
        ]:
            val_raw = latest.get(field, 0)
            try:
                val_f = float(val_raw) if pd.notnull(val_raw) else 0.0
            except (ValueError, TypeError):
                val_f = 0.0
            prev_raw = prev.get(field, val_f)
            try:
                prev_f = float(prev_raw) if pd.notnull(prev_raw) else val_f
            except (ValueError, TypeError):
                prev_f = val_f
            flag_label, flag_color = metric_flag(field, val_f)
            col.metric(
                label=f"{icon} {label}", value=f"{int(val_f)}",
                delta=int(val_f - prev_f) if len(df) >= 2 else None,
                delta_color="inverse",
            )
            col.markdown(f":{flag_color}[{flag_label}]")

        latest_risk_val = float(latest.get("Health_Risk_Score", 0) or 0)
        if latest_risk_val >= 85:
            last_risk_alert = st.session_state.get("_last_risk_alert_ts", 0)
            now_ts = time.time()
            if now_ts - last_risk_alert > 60:
                st.session_state._last_risk_alert_ts = now_ts
                delivered = fire_emergency_webhook({"alert": "high_risk_score", "score": int(latest_risk_val), "patient": st.session_state.active_patient})
                st.error(
                    "🚨 **CRITICAL RISK THRESHOLD EXCEEDED** 🚨\\n\\nScore is >= 85. "
                    f"{'Preventative webhook notified.' if delivered else 'Webhook did not confirm delivery.'}"
                )"""

if old_latest_readings in content:
    content = content.replace(old_latest_readings, new_latest_readings, 1)
    print("Replaced latest readings successfully")
else:
    print("WARNING: latest readings not found")

# 9. Update Health Coach inference call to use call_gemini_with_fallback
coach_start = 'with st.spinner(f"🧠 Health Coach is analysing your biometric trends in {st.session_state.app_language}..."):\\n'
coach_old = """        with st.spinner(f"🧠 Health Coach is analysing your biometric trends in {st.session_state.app_language}..."):
            try:
                lang_coach_instruction = HEALTH_COACH_SYSTEM_INSTRUCTION + f"\\n\\nCRITICAL: You must provide your 3-bullet-point wellness recommendation and the CDSCO disclaimer entirely in {st.session_state.app_language}."
                response = client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=coach_prompt,
                    config=types.GenerateContentConfig(system_instruction=lang_coach_instruction),
                )
                active_record["coach_recommendation"] = response.text
            except Exception as exc:
                logger.error("Gemini health coach call failed: %s", exc)
                active_record["coach_recommendation"] = f"⚠️ **Gemini API error:** `{exc}`" """

coach_new = """        with st.spinner(f"🧠 Health Coach is analysing your biometric trends in {st.session_state.app_language}..."):
            try:
                lang_coach_instruction = HEALTH_COACH_SYSTEM_INSTRUCTION + f"\\n\\nCRITICAL: You must provide your 3-bullet-point wellness recommendation and the CDSCO disclaimer entirely in {st.session_state.app_language}."
                response_text, used_model = call_gemini_with_fallback(
                    client=client,
                    contents=coach_prompt,
                    system_instruction=lang_coach_instruction,
                )
                active_record["coach_recommendation"] = response_text
            except Exception as exc:
                logger.error("Gemini health coach call failed: %s", exc)
                active_record["coach_recommendation"] = f"⚠️ **Gemini API error:** `{exc}`" """

if coach_old.strip() in content:
    content = content.replace(coach_old.strip(), coach_new.strip(), 1)
    print("Replaced coach call successfully")
else:
    c_idx = content.find("with st.spinner(f\"🧠 Health Coach")
    if c_idx != -1:
        c_end_marker = 'active_record["coach_recommendation"] = f"⚠️ **Gemini API error:** `{exc}`"'
        c_end = content.find(c_end_marker, c_idx) + len(c_end_marker)
        content = content[:c_idx] + coach_new.strip() + content[c_end:]
        print("Replaced coach call via index search successfully")
    else:
        print("WARNING: coach call not found")

# 10. Update Tab 4 Reminders status indicator
old_reminders_status = 'row[0].markdown(f"{\\\'🔴\\\' if overdue else \\\'🟢\\\' if r[\\\'done\\\'] else \\\'🟡\\\'} **{r[\\\'date\\\']}**")'
new_reminders_status = 'status_badge = "🟢 Done" if r["done"] else ("🔴 Overdue" if overdue else "🟡 Pending")\n            row[0].markdown(f"**{r[\'date\']}**\\n\\n{status_badge}")'

old_rem_slice = """            rid = r["id"]
            overdue = (not r["done"]) and r["date"] < today_str
            row = st.columns([1, 4, 1, 1])
            row[0].markdown(f"{'🔴' if overdue else '🟢' if r['done'] else '🟡'} **{r['date']}**")"""

new_rem_slice = """            rid = r["id"]
            overdue = (not r["done"]) and r["date"] < today_str
            is_today = (not r["done"]) and r["date"] == today_str
            row = st.columns([1.5, 4, 1, 1])
            status_badge = "🟢 Completed" if r["done"] else ("🔴 Overdue" if overdue else ("🟠 Due Today" if is_today else "🟡 Upcoming"))
            row[0].markdown(f"**{r['date']}**<br/>`{status_badge}`", unsafe_allow_html=True)"""

if old_rem_slice in content:
    content = content.replace(old_rem_slice, new_rem_slice, 1)
    print("Replaced Reminders slice successfully")
else:
    print("WARNING: Reminders slice not found")

# Restore original CRLF if was present
if has_crlf:
    content = content.replace("\n", "\r\n")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(content)

print("All updates written successfully!")
