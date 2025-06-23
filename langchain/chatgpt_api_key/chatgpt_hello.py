import openai

from _settings.config import OPENAI_KEY

# 여기에 본인의 API Key 입력
openai.api_key = OPENAI_KEY

response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # 또는 gpt-3.5-turbo, gpt-4o
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Colab에서 GPT를 쓰는 방법 알려줘"},
    ]
)

print(response['choices'][0]['message']['content'])