import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# โหลดค่า API Key จาก .env
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API"))

model = genai.GenerativeModel("gemini-1.5-flash")

def get_data():
    prompt = prompt = """
    You are a quiz riddle generator.
    Create exactly 1 quick and interesting riddle for my audience to solve.
    The riddle should be easy enough to engage and entertain the participants.
    Each riddle must have three options and only one correct answer.

    Return ONLY a valid JSON array with exactly 5 string elements in this order:
    ["Hook", "Option1", "Option2", "Option3", "Answer"]

    Example:
    ["What has an eye, but cannot see?", "A needle", "A hurricane", "A potato", "A needle"]

    Do not include any extra text, explanation, markdown, code fences, or formatting — only the JSON array itself.
    Please ensure that your riddles are well-craft, engaging, and provide a satisfying solution.
    """


    response = model.generate_content(prompt)

    try:
        data = json.loads(response.text)
        if isinstance(data, list) and len(data) == 5:
            return data
        else:
            raise ValueError(f"Expected 5 elements, got {len(data)}: {data}")
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON Decode Error: {e}\nRaw output: {response.text}")
    
# ทดสอบรันไฟล์นี้ตรง ๆ
if __name__ == "__main__":
    print(get_data())
