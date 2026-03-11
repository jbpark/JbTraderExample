import google.generativeai as genai

from _settings.config import GEMINI_KEY

genai.configure(api_key=GEMINI_KEY)  # 발급받은 API 키 입력

model = genai.GenerativeModel("gemini-2.0-flash")

response = model.generate_content("한국의 수도는 어디인가요?")

print(response.text)
