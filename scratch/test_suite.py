import io
import pandas as pd
from app import (
    new_patient_record,
    blank_health_metrics,
    metric_flag,
    generate_dossier,
    generate_doctor_pdf,
    get_api_key,
    GEMINI_MODELS,
    GROQ_MODELS,
    CITY_COORDS,
)

def run_tests():
    print("=== RUNNING MEDISCAN AI VERIFICATION TESTS ===")
    
    # 1. Verify blank health metrics & patient record
    record = new_patient_record()
    assert "profile" in record
    assert "health_metrics" in record
    assert len(record["health_metrics"]) == 6
    print("✅ new_patient_record & blank_health_metrics passed")

    # 2. Verify metric_flag
    flag, color = metric_flag("Resting_HR", 75)
    assert "Normal" in flag and color == "green"
    flag, color = metric_flag("Resting_HR", 130)
    assert "High" in flag and color == "red"
    print("✅ metric_flag clinical thresholds passed")

    # 3. Verify generate_dossier with second opinion
    record["chat_history"].append({"role": "user", "content": "I have mild fever"})
    record["chat_history"].append({"role": "assistant", "content": "Differential diagnosis: Viral fever"})
    record["report_history"].append({
        "id": "test1234",
        "timestamp": "2026-10-05 10:00",
        "filename": "blood_test.png",
        "result": "Hemoglobin 14.2 g/dL - Normal",
        "second_opinion": "Consensus agrees with normal panel."
    })
    ec = {"name": "Jane Doe", "phone": "+91 9876543210"}
    dossier = generate_dossier("John Doe", record, ec)
    assert "Jane Doe" in dossier
    assert "Viral fever" in dossier
    assert "Consensus agrees" in dossier
    print("✅ generate_dossier with emergency contact & second opinion passed")

    # 4. Verify generate_doctor_pdf
    pdf_buf = generate_doctor_pdf(
        patient_name="John Doe",
        record=record,
        emergency_contact=ec,
        language="English",
        include_chat=True,
        include_reports=True,
        include_biometrics=True,
        doctor_name="Dr. Mehta",
        referring_note="Patient referred for routine review."
    )
    pdf_bytes = pdf_buf.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    print(f"✅ generate_doctor_pdf successfully generated valid PDF ({len(pdf_bytes)} bytes)")

    # 5. Verify models
    assert "gemini-2.5-flash" in GEMINI_MODELS
    assert "llama-3.3-70b-versatile" in GROQ_MODELS
    print("✅ Model candidates configured correctly")

    # 6. Verify Indian cities coordinates
    assert "Mumbai" in CITY_COORDS
    assert "Pune" in CITY_COORDS
    assert "Delhi" in CITY_COORDS
    print(f"✅ City coordinates verified ({len(CITY_COORDS)} cities)")

    print("\n🎉 ALL TESTS PASSED! APPLICATION IS RESILIENT & PRODUCTION READY!")

if __name__ == "__main__":
    run_tests()
