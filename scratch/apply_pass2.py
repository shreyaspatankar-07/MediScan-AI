import re

app_path = r"c:\Users\SHREYAS\Desktop\MediScan-AI-main\app.py"

with open(app_path, "r", encoding="utf-8") as f:
    code = f.read()

# 1. Update generate_doctor_pdf
old_pdf_func = """def generate_doctor_pdf(patient_name, record, emergency_contact, language,
                         include_chat=True, include_reports=True, include_biometrics=True,
                         doctor_name="", referring_note=""):
    \"\"\"Builds an in-memory PDF clinical handoff summary for a doctor. Returns BytesIO.\"\"\"
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
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=10, leading=14)
    tag = ParagraphStyle("tag", parent=styles["Normal"], fontSize=9, textColor=colors.HexColor("#b02a2a"))

    def esc(text):
        return (str(text) or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

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
    prof = record["profile"]
    profile_table_data = [
        ["Name", esc(patient_name)],
        ["Age", esc(prof.get("age", "—"))],
        ["Sex", esc(prof.get("sex", "—"))],
        ["Weight", f"{prof.get('weight_kg', 0):.1f} kg" if prof.get("weight_kg") else "—"],
        ["Chronic Conditions", esc(prof.get("chronic_conditions") or "None reported")],
    ]
    if emergency_contact.get("name"):
        profile_table_data.append(["Emergency Contact", f"{esc(emergency_contact['name'])} — {esc(emergency_contact.get('phone', ''))}"])
    pt = Table(profile_table_data, colWidths=[1.7 * inch, 4.3 * inch])
    pt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f8")),
        ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#c9d6e3")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(pt)

    # ── Structured Intake (most recent) ────────────────────────────────────
    intake = record.get("last_intake")
    if intake:
        story.append(Paragraph("Most Recent Structured Intake", h2))
        intake_data = [
            ["Severity", f"{intake.get('severity', '—')}/10"],
            ["Duration", esc(intake.get("duration", "—"))],
            ["Onset", esc(intake.get("onset", "—"))],
            ["Affected Area(s)", esc(", ".join(intake.get("body_areas", [])) or "Not specified")],
        ]
        it = Table(intake_data, colWidths=[1.7 * inch, 4.3 * inch])
        it.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#eef3f8")),
            ("FONTSIZE", (0, 0), (-1, -1), 9.5),
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
        bt = Table(rows, colWidths=[1.0 * inch] * 5)
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
        flag_label, _ = metric_flag("Health_Risk_Score", latest["Health_Risk_Score"])
        story.append(Paragraph(f"Latest Health Risk Score: <b>{int(latest['Health_Risk_Score'])}/100</b> ({esc(flag_label)})", body))

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
            style = body
            text = esc(m["content"]).replace("\\n", "<br/>")
            story.append(Paragraph(f"<b>{role_label}:</b> {text}", style))
            story.append(Spacer(1, 6))

    # ── Report / Lab Analysis History ──────────────────────────────────────
    if include_reports and record["report_history"]:
        story.append(PageBreak())
        story.append(Paragraph("Lab / Visual Report Analyses", h2))
        for r in record["report_history"]:
            story.append(Paragraph(f"<b>{esc(r['filename'])}</b> — {esc(r['timestamp'])}", body))
            text = esc(r["result"]).replace("\\n", "<br/>")
            story.append(Paragraph(text, body))
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
    return buf"""

new_pdf_func = """def generate_doctor_pdf(patient_name, record, emergency_contact, language,
                         include_chat=True, include_reports=True, include_biometrics=True,
                         doctor_name="", referring_note=""):
    \"\"\"Builds an in-memory PDF clinical handoff summary for a doctor. Returns BytesIO.\"\"\"
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
            content = re.sub(r'```json\\s*\\{.*?\\}\\s*```', '', content, flags=re.DOTALL)
            text = esc(content).replace("\\n", "<br/>")
            story.append(Paragraph(f"<b>{role_label}:</b> {text}", body))
            story.append(Spacer(1, 6))

    # ── Report / Lab Analysis History ──────────────────────────────────────
    if include_reports and record["report_history"]:
        story.append(PageBreak())
        story.append(Paragraph("Lab / Visual Report Analyses", h2))
        for r in record["report_history"]:
            story.append(Paragraph(f"<b>{esc(r['filename'])}</b> — {esc(r['timestamp'])}", body))
            text = esc(r["result"]).replace("\\n", "<br/>")
            story.append(Paragraph(text, body))
            if r.get("second_opinion"):
                story.append(Spacer(1, 4))
                so_text = esc(r["second_opinion"]).replace("\\n", "<br/>")
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
    return buf"""

if old_pdf_func in code:
    code = code.replace(old_pdf_func, new_pdf_func, 1)
    print("Replaced generate_doctor_pdf successfully")
else:
    print("WARNING: generate_doctor_pdf not found exactly")

# 2. Update generate_dossier & Sidebar
old_sidebar_dossier = """    def generate_dossier(patient_name: str, record: dict) -> str:
        \"\"\"Build a plain-text patient dossier string for download/export.\"\"\"
        prof = record["profile"]
        content = f"=== MEDISCAN AI PATIENT DOSSIER: {patient_name} ===\\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n\\n"
        content += f"PROFILE:\\nAge: {prof.get('age')}\\nSex: {prof.get('sex')}\\nWeight: {prof.get('weight_kg')} kg\\nConditions: {prof.get('chronic_conditions')}\\n\\n"
        if st.session_state.emergency_contact["name"]:
            content += f"EMERGENCY CONTACT:\\n{st.session_state.emergency_contact['name']} — {st.session_state.emergency_contact['phone']}\\n\\n"
        if not record["health_metrics"].empty:
            content += f"BIOMETRIC TRAJECTORY (Last 6 Months):\\n{record['health_metrics'].to_string(index=False)}\\n\\n"
        if record["report_history"]:
            content += "LAB / VISUAL REPORT HISTORY:\\n"
            for r in record["report_history"]:
                content += f"\\n--- {r['timestamp']} ({r['filename']}) ---\\n{r['result']}\\n"
        if record["coach_recommendation"]:
            content += f"\\nLATEST WELLNESS COACH RECOMMENDATION:\\n{record['coach_recommendation']}\\n"
        if record["chat_history"]:
            content += "\\nSYMPTOM TRIAGE CHAT LOG:\\n"
            for m in record["chat_history"]:
                content += f"[{m['role'].upper()}] {m['content']}\\n\\n"
        return content

    # DESIGN NOTE: Lazy dossier generation capturing local variables outside the closure to ensure safe context handling without accessing st.session_state inside the deferred callable.
    _active_name = st.session_state.active_patient
    _active_record = st.session_state.patients[_active_name]
    _all_patients_snapshot = dict(st.session_state.patients)

    st.download_button(
        "📥 Download Active Patient Dossier",
        data=lambda name=_active_name, record=_active_record: generate_dossier(name, record),
        file_name=f"mediscan_dossier_{_active_name.replace(' ', '_')}.txt",
        mime="text/plain", use_container_width=True, type="secondary",
    )

    st.download_button(
        "📥 Download All Patients Dossier",
        data=lambda pts=_all_patients_snapshot: "\\n\\n".join(generate_dossier(n, r) for n, r in pts.items()),
        file_name="mediscan_dossier_all_patients.txt",
        mime="text/plain", use_container_width=True,
    )"""

new_sidebar_dossier = """    def generate_dossier(patient_name: str, record: dict, emergency_contact: dict = None) -> str:
        \"\"\"Build a plain-text patient dossier string for download/export.\"\"\"
        if emergency_contact is None:
            emergency_contact = {}
        prof = record.get("profile", {})
        content = f"=== MEDISCAN AI PATIENT DOSSIER: {patient_name} ===\\n"
        content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\\n\\n"
        content += f"PROFILE:\\nAge: {prof.get('age', '—')}\\nSex: {prof.get('sex', '—')}\\nWeight: {prof.get('weight_kg', '—')} kg\\nConditions: {prof.get('chronic_conditions') or 'None'}\\n\\n"
        if emergency_contact.get("name"):
            content += f"EMERGENCY CONTACT:\\n{emergency_contact['name']} — {emergency_contact.get('phone', '')}\\n\\n"
        if not record["health_metrics"].empty:
            content += f"BIOMETRIC TRAJECTORY (Last 6 Months):\\n{record['health_metrics'].to_string(index=False)}\\n\\n"
        if record.get("report_history"):
            content += "LAB / VISUAL REPORT HISTORY:\\n"
            for r in record["report_history"]:
                content += f"\\n--- {r['timestamp']} ({r['filename']}) ---\\n{r['result']}\\n"
                if r.get("second_opinion"):
                    content += f"\\n[SECOND OPINION CONSENSUS]\\n{r['second_opinion']}\\n"
        if record.get("coach_recommendation"):
            content += f"\\nLATEST WELLNESS COACH RECOMMENDATION:\\n{record['coach_recommendation']}\\n"
        if record.get("chat_history"):
            content += "\\nSYMPTOM TRIAGE CHAT LOG:\\n"
            for m in record["chat_history"]:
                content += f"[{m['role'].upper()}] {m['content']}\\n\\n"
        return content

    _active_name = st.session_state.active_patient
    _active_record = st.session_state.patients[_active_name]
    _active_ec = dict(st.session_state.emergency_contact)
    _all_patients_snapshot = {k: dict(v) for k, v in st.session_state.patients.items()}

    st.download_button(
        "📥 Download Active Patient Dossier",
        data=lambda name=_active_name, record=_active_record, ec=_active_ec: generate_dossier(name, record, ec),
        file_name=f"mediscan_dossier_{_active_name.replace(' ', '_')}.txt",
        mime="text/plain", use_container_width=True, type="secondary",
    )

    st.download_button(
        "📥 Download All Patients Dossier",
        data=lambda pts=_all_patients_snapshot, ec=_active_ec: "\\n\\n".join(generate_dossier(n, r, ec) for n, r in pts.items()),
        file_name="mediscan_dossier_all_patients.txt",
        mime="text/plain", use_container_width=True,
    )"""

if old_sidebar_dossier in code:
    code = code.replace(old_sidebar_dossier, new_sidebar_dossier, 1)
    print("Replaced dossier generation block successfully")
else:
    print("WARNING: dossier generation block not found exactly")

# 3. Add API Settings Expander and Backup/Restore in Sidebar
old_sidebar_top = """with st.sidebar:
    st.markdown("### 🌐 Language Preferences")
    st.session_state.app_language = st.selectbox(
        "Select Response Language",
        list(LANG_MAP.keys()),
        index=list(LANG_MAP.keys()).index(st.session_state.app_language),
    )

    if not _api_ready:
        st.warning(
            "⚠️ **Gemini API key not configured.**\\n\\nAdd `GEMINI_API_KEY` to `.streamlit/secrets.toml`. Report analysis will be unavailable until then.",
            icon="🔑",
        )
    if groq_client is None:
        st.warning(
            "⚠️ **Groq API key not configured.**\\n\\nAdd `GROQ_API_KEY` to `.streamlit/secrets.toml`. Voice input (Whisper STT) will be unavailable until then.",
            icon="🔑",
        )"""

new_sidebar_top = """with st.sidebar:
    st.markdown("### 🌐 Language Preferences")
    st.session_state.app_language = st.selectbox(
        "Select Response Language",
        list(LANG_MAP.keys()),
        index=list(LANG_MAP.keys()).index(st.session_state.app_language),
    )

    with st.expander("🔑 API Keys & System Connectivity", expanded=not _api_ready):
        st.caption("Provide credentials here or via `.streamlit/secrets.toml` or system environment variables.")
        c_gem_status = "🟢 Connected" if _api_ready else "🔴 Missing Key"
        c_groq_status = "🟢 Connected" if groq_client else "🔴 Missing Key"
        st.markdown(f"- **Gemini AI:** `{c_gem_status}`\\n- **Groq Whisper:** `{c_groq_status}`")
        custom_gem = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.get("custom_GEMINI_API_KEY", ""),
            placeholder="AIzaSy...",
            key="input_gemini_key",
        )
        custom_groq = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.get("custom_GROQ_API_KEY", ""),
            placeholder="gsk_...",
            key="input_groq_key",
        )
        custom_hook = st.text_input(
            "Alert Webhook URL",
            value=st.session_state.get("custom_webhook_url", EMERGENCY_WEBHOOK_URL),
            placeholder="https://...",
            key="input_webhook_url",
        )
        if st.button("💾 Apply API Settings", use_container_width=True, type="primary"):
            st.session_state["custom_GEMINI_API_KEY"] = custom_gem.strip()
            st.session_state["custom_GROQ_API_KEY"] = custom_groq.strip()
            st.session_state["custom_webhook_url"] = custom_hook.strip()
            st.success("API credentials saved!")
            st.rerun()"""

if old_sidebar_top in code:
    code = code.replace(old_sidebar_top, new_sidebar_top, 1)
    print("Replaced sidebar top with API settings expander")
else:
    print("WARNING: sidebar top not found exactly")

# 4. Add Clear new_patient_name in Sidebar patient creation
old_add_patient = """        if cadd.button("Add Patient", use_container_width=True):
            if new_name and new_name not in st.session_state.patients:
                st.session_state.patients[new_name] = new_patient_record()
                st.session_state.active_patient = new_name
                st.rerun()"""

new_add_patient = """        if cadd.button("Add Patient", use_container_width=True):
            if new_name and new_name not in st.session_state.patients:
                st.session_state.patients[new_name] = new_patient_record()
                st.session_state.active_patient = new_name
                st.session_state["new_patient_name"] = ""
                st.rerun()"""

if old_add_patient in code:
    code = code.replace(old_add_patient, new_add_patient, 1)
    print("Replaced Add Patient with clear input")
else:
    print("WARNING: Add Patient not found exactly")

# 5. Add Session Backup/Restore to Sidebar
old_sys_arch = """    st.markdown("---")
    with st.expander("⚙️ System Architecture"):"""

new_backup_arch = """    st.markdown("---")
    with st.expander("💾 Clinical Data Backup & Restore"):
        st.caption("Export patient profiles, medical histories, and reminders to JSON or restore a prior backup.")
        backup_dict = {
            "patients": {
                name: {
                    "profile": p["profile"],
                    "chat_history": p.get("chat_history", []),
                    "archived_conversations": p.get("archived_conversations", []),
                    "report_history": p.get("report_history", []),
                    "health_metrics": p["health_metrics"].to_dict(orient="records"),
                    "coach_recommendation": p.get("coach_recommendation"),
                }
                for name, p in st.session_state.patients.items()
            },
            "reminders": st.session_state.reminders,
            "emergency_contact": st.session_state.emergency_contact,
            "backup_date": datetime.now().isoformat(),
        }
        st.download_button(
            "💾 Download All Records (JSON)",
            data=json.dumps(backup_dict, indent=2),
            file_name=f"mediscan_backup_{date.today().isoformat()}.json",
            mime="application/json",
            use_container_width=True,
        )
        restore_file = st.file_uploader("📂 Restore Records from Backup", type=["json"], key="restore_uploader")
        if restore_file is not None:
            if st.button("Apply Restored Records", use_container_width=True):
                try:
                    loaded = json.load(restore_file)
                    if "patients" in loaded:
                        restored_pts = {}
                        for pname, pdata in loaded["patients"].items():
                            rec = new_patient_record()
                            rec["profile"] = pdata.get("profile", rec["profile"])
                            rec["chat_history"] = pdata.get("chat_history", [])
                            rec["archived_conversations"] = pdata.get("archived_conversations", [])
                            rec["report_history"] = pdata.get("report_history", [])
                            if "health_metrics" in pdata:
                                rec["health_metrics"] = pd.DataFrame(pdata["health_metrics"])
                            rec["coach_recommendation"] = pdata.get("coach_recommendation")
                            restored_pts[pname] = rec
                        st.session_state.patients = restored_pts
                        st.session_state.active_patient = list(restored_pts.keys())[0]
                    if "reminders" in loaded:
                        st.session_state.reminders = loaded["reminders"]
                    if "emergency_contact" in loaded:
                        st.session_state.emergency_contact = loaded["emergency_contact"]
                    st.success("✅ Clinical records restored successfully!")
                    st.rerun()
                except Exception as b_err:
                    st.error(f"Restore failed: {b_err}")

    st.markdown("---")
    with st.expander("⚙️ System Architecture"):"""

if old_sys_arch in code:
    code = code.replace(old_sys_arch, new_backup_arch, 1)
    print("Replaced system architecture with backup/restore expander")
else:
    print("WARNING: system architecture block not found exactly")

with open(app_path, "w", encoding="utf-8") as f:
    f.write(code)

print("Pass 2 written successfully")
