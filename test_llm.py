from google import genai
client = genai.Client()
response = client.models.generate_content(
    model='gemini-2.5-flash',
    contents='Tell me a short joke.'
)
print(response.text)
