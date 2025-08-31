import re
import json
import uuid
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://riddles-api.vercel.app/random"
)
MODEL_NAME = "deepseek-chat"  # โมเดลที่ใช้

SYSTEM_PROMPT = (
    "You are a Philosophical Questions quiz riddle generator.\n"
    "Return ONLY a valid JSON array with exactly 5 string elements in this order:\n"
    '["Hook", "Option1", "Option2", "Option3", "Answer"]\n'
    "No explanations, no markdown, no code fences, no extra text.\n"
    "Do not return JSON object. Do not include keys. Do not include any text before or after the array.\n"
    "Each element must contain meaningful text for a real riddle.\n"
    "The 'Hook' must be a clear and logical riddle question.\n"
    "Option1-3 must all be possible answers, but only one is logically correct.\n"
    "The 'Answer' must be exactly identical to one of the three options.\n"
    "The 'Answer' must always be the logically correct choice, not random.\n"
    "Avoid repeating riddles that have already appeared in this session.\n"
    "The riddle should be thought-provoking and slightly challenging, not trivial.\n"
)

USER_PROMPT = f"""
Create exactly 1 philosophical riddle for my audience.
- Must be logical and solvable.
- Must have 3 distinct options, only one is correct.
- The correct answer must appear exactly as one of the three options.
- Avoid repeating riddles.
- Make it thought-provoking and not too obvious.

Examples:
["What has an eye, but cannot see?", "A needle", "A hurricane", "A potato", "A needle"]
["I speak without a mouth and hear without ears. What am I?", "An echo", "A shadow", "A dream", "An echo"]

Session ID: {uuid.uuid4()}
"""

def safe_json_loads(text):
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    cleaned = re.sub(r"\n?```$", "", cleaned).strip()
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return [
                data.get("hook", ""),
                data.get("option1", ""),
                data.get("option2", ""),
                data.get("option3", ""),
                data.get("answer", "")
            ]
        return data
    except json.JSONDecodeError:
        match = re.search(r"\[[^\[\]]*\]", cleaned, re.DOTALL)
        if match:
            return json.loads(match.group(0))
    raise ValueError(f"JSON Decode Error\nRaw after clean: {cleaned}")

def generate_riddle(retry=True):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": USER_PROMPT},
        ],
        stream=False
    )
    text = response.choices[0].message.content.strip()
    quiz_data = safe_json_loads(text)

    if len(quiz_data) < 5:
        raise ValueError(f"Invalid format: {quiz_data}")

    hook = quiz_data[0]
    options = quiz_data[1:4]
    answer = quiz_data[4]

    # ถ้า answer ไม่อยู่ใน options ให้ retry
    if answer not in options and retry:
        retry_prompt = f"""
        The previous riddle output had an answer that was not in the options.
        Please only return a valid JSON array in the format:
        ["Hook", "Option1", "Option2", "Option3", "Answer"]
        Make sure the 'Answer' is exactly one of the three options.
        Previous output: {quiz_data}
        """
        return generate_riddle_from_text(retry_prompt)

    if answer not in options:
        answer = options[0]  # fallback
    return [hook] + options + [answer]

def generate_riddle_from_text(prompt_text):
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt_text}],
        stream=False
    )
    text = response.choices[0].message.content.strip()
    return generate_riddle_from_text_direct(text)

def generate_riddle_from_text_direct(text):
    quiz_data = safe_json_loads(text)
    hook = quiz_data[0]
    options = quiz_data[1:4]
    answer = quiz_data[4]
    if answer not in options:
        answer = options[0]
    return [hook] + options + [answer]

if __name__ == "__main__":
    print(json.dumps(generate_riddle(), ensure_ascii=False, indent=2))
