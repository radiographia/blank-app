import streamlit as st
import requests
import base64
import json

# App page configurations
st.set_page_config(page_title="Радиография ИИ", page_icon="🩺", layout="centered")

st.title("🩺 Медицинский ИИ-Регистратор")
st.write("Загрузите аудиозапись приема (MP3), чтобы сгенерировать структурированную медицинскую карту.")

# Secure Key Retrieval: Checks Streamlit Secrets first, falls back to manual input
if "OPENROUTER_API_KEY" in st.secrets:
    api_key = st.secrets["OPENROUTER_API_KEY"]
else:
    api_key = st.text_input("Ключ OpenRouter API не найден в Secrets. Введите вручную:", type="password")

uploaded_file = st.file_uploader("Шаг 1: Загрузите аудиофайл врача (.mp3)", type=["mp3"])

if st.button("🚀 Шаг 2: Начать структурирование") and uploaded_file:
    if not api_key:
        st.error("Пожалуйста, предоставьте валидный API ключ.")
    else:
        try:
            # 1. Read and encode file
            audio_bytes = uploaded_file.read()
            audio_base64 = base64.b64encode(audio_bytes).decode("utf-8")
            
            # 2. Setup prompt instructions
            prompt = (
                "Ты — профессиональный медицинский ИИ-ассистент. Прослушай аудиозапись врача на русском языке. "
                "Распознай речь и сформируй структурированную медицинскую карту строго в формате JSON. "
                "Схема ответа должна содержать следующие ключи:\n"
                "{\n"
                "  'Жалобы': 'подробный список жалоб',\n"
                "  'Анамнез': 'анамнез заболевания и жизни',\n"
                "  'Объективный_статус': 'данные осмотра, пульс, давление, пальпация',\n"
                "  'Предварительный_диагноз': 'четкий диагноз на русском',\n"
                "  'Код_МКБ10': 'найди и подбери точный код по классификации МКБ-10'\n"
                "}\n"
                "Не пиши никаких вступлений, рассуждений или тегов типа ```json. Только чистый JSON объект."
            )
            
            # 3. Request payload for Free Gemini on OpenRouter
            payload = {
                "model": "google/gemini-2.5-flash-lite-preview-09-2025",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "input_audio",
                                "input_audio": {"data": audio_base64, "format": "mp3"}
                            }
                        ]
                    }
                ],
                "response_format": {"type": "json_object"}
            }
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://streamlit.app",
                "X-Title": "Radiographia Medical App"
            }
            
            # 4. API Request Execution
            with st.spinner("🔄 ИИ слушает аудиозапись и заполняет карту... Пожалуйста, подождите."):
                res = requests.post("https://openrouter.ai", headers=headers, json=payload)
                
                if res.status_code == 200:
                    response_data = res.json()
                    raw_text = response_data['choices']['message']['content']
                    result_json = json.loads(raw_text)
                    
                    st.success("🎉 Успешно обработано!")
                    
                    # 5. Render beautiful structured UI blocks for doctors
                    for section, content in result_json.items():
                        st.subheader(f"📍 {section.replace('_', ' ')}")
                        st.info(content if content else "Данные не указаны в аудиозаписи")
                        
                    # Also give them raw JSON if they need to copy it into their EMR system
                    with st.expander("Посмотреть исходный JSON для вставки в медкарту"):
                        st.json(result_json)
                else:
                    st.error(f"Ошибка API ({res.status_code}): {res.text}")
                    
        except Exception as e:
            st.error(f"Произошла непредвиденная ошибка: {str(e)}")
