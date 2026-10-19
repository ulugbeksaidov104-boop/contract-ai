import streamlit as st
import json
from google import genai
from pypdf import PdfReader

# Sahifa sozlamalari
st.set_page_config(page_title="AI Shartnoma Tahlilchisi", page_icon="⚖️", layout="wide")

st.title("⚖️ Shartnoma Tahlilchisi (Gemini AI)")
st.write("PDF formatidagi shartnomani yuklang, AI undagi xavfli shartlar va noqulay bandlarni tahlil qilib beradi.")

# API kalitni Streamlit Secrets bo'limidan olish
api_key = st.secrets.get("GEMINI_API_KEY")

if not api_key:
    st.error("GEMINI_API_KEY topilmadi. Iltimos, Streamlit Secrets bo'limiga API kalitni kiriting.")
    st.stop()

# Gemini mijozi
client = genai.Client(api_key=api_key)

def extract_text_from_pdf(pdf_file):
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text

def analyze_contract(contract_text):
    prompt = f"""
    Sen professional yurist va mustaqil shartnoma tahlilchisisan.
    Quyidagi shartnoma matnini 'Buyurtmachi/Mijoz' manfaati nuqtai nazaridan chuqur tahlil qil.
    Xavfli, noqonuniy yoki bir tomonlama noqulay shartlarni aniqla.
    
    Javobni faqat va faqat quyidagi qat'iy JSON formatida qaytar (boshqa hech qanday izoh qo'shma):
    {{
      "summary": "Shartnomaning umumiy qisqacha mazmuni",
      "risk_score": "Yuqori / O'rta / Past",
      "issues": [
        {{
          "clause": "Shartnomadagi xavfli matn yoki band",
          "reason": "Nima uchun xavfli?",
          "solution": "Qanday o'zgartirish kerak?"
        }}
      ]
    }}

    Shartnoma matni:
    {contract_text[:15000]}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={
            "response_mime_type": "application/json"
        }
    )
    return json.loads(response.text)

# Fayl yuklash interfeysi
uploaded_file = st.file_uploader("Shartnoma faylini tanlang (faqat PDF)", type=["pdf"])

if uploaded_file is not None:
    if st.button("Hujjatni tahlil qilish"):
        with st.spinner("AI shartnomani o'rganmoqda, iltimos kuting..."):
            extracted_text = extract_text_from_pdf(uploaded_file)
            
            if not extracted_text.strip():
                st.error("PDF ichidan matn ajratib bo'lmadi (ehtimol skaner qilingan rasm).")
            else:
                try:
                    result = analyze_contract(extracted_text)
                    
                    st.subheader("📋 Umumiy xulosa")
                    st.write(result.get("summary", ""))
                    
                    risk = result.get("risk_score", "Noma'lum")
                    if "Yuqori" in risk:
                        st.error(f"Xavf darajasi: {risk}")
                    elif "O'rta" in risk:
                        st.warning(f"Xavf darajasi: {risk}")
                    else:
                        st.success(f"Xavf darajasi: {risk}")
                    
                    st.divider()
                    st.subheader("⚠️ Aniqlangan xavfli bandlar")
                    
                    issues = result.get("issues", [])
                    if not issues:
                        st.info("Hech qanday jiddiy xavf aniqlanmadi.")
                    else:
                        for idx, issue in enumerate(issues, 1):
                            with st.expander(f"{idx}. {issue.get('clause')[:70]}..."):
                                st.write(f"**Asl band:** {issue.get('clause')}")
                                st.write(f"**Xavf sababi:** {issue.get('reason')}")
                                st.success(f"**Tavsiya qilingan tuzatish:** {issue.get('solution')}")
                except Exception as e:
                    st.error(f"Xatolik yuz berdi: {e}")