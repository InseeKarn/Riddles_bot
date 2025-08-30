import requests, re, json, uuid


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "zephyr:7b-alpha"  # เปลี่ยนตรงนี้ถ้าจะใช้โมเดลอื่น

SYSTEM_PROMPT = (
    "You are a quiz riddle generator.\n"
    "Return ONLY a valid JSON array with exactly 5 string elements in this order:\n"
    '["Hook", "Option1", "Option2", "Option3", "Answer"]\n'
    "No explanations, no markdown, no code fences, no extra text.\n"
    "Do not return JSON object. Do not include keys. Do not include any text before or after the array.\n"
    "Each element must contain meaningful text for a real riddle.\n"
    "The 'Hook' is the riddle question, 'Option1-3' are possible answers, and 'Answer' is the correct one.\n"
    "The Answer must be exactly one of Option1, Option2, or Option3.\n"
    "Do not add more than three options.\n"
)  

unique_id = uuid.uuid4()
USER_PROMPT = f"""
Create exactly 1 quick and interesting riddle for my audience to solve.
The riddle should be challenging enough to engage the participants.
Each riddle must have three options and only one correct answer.
The correct answer must be exactly one of the three options.

Examples:
["What has an eye, but cannot see?", "A needle", "A hurricane", "A potato", "A needle"]
["I speak without a mouth and hear without ears. What am I?", "An echo", "A shadow", "A dream", "An echo"]

Now create a new one with different content. Session ID: {unique_id}
"""

def safe_json_loads(text):
    # ลบ code fence และ markdown
    cleaned = re.sub(r"^```[a-zA-Z]*\n?", "", text)
    cleaned = re.sub(r"\n?```$", "", cleaned)
    cleaned = cleaned.strip()

    # ลอง parse ตรง ๆ ก่อน
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            # แปลง dict -> array ตามลำดับที่ต้องการ
            return [
                data.get("hook", ""),
                data.get("option1", ""),
                data.get("option2", ""),
                data.get("option3", ""),
                data.get("answer", "")
            ]
        return data
    except json.JSONDecodeError:
        pass

    # ถ้า parse ไม่ได้ ลองดึง array จากข้อความ
    match = re.search(r"\[[^\[\]]*\]", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"JSON Decode Error\nRaw after clean: {cleaned}")

def get_data():
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL_NAME,
            "system": SYSTEM_PROMPT,
            "prompt": USER_PROMPT,
            "stream": False,
            "options": {
                "temperature": 0.9,
                "top_p": 0.9,
                "repeat_penalty": 1.1
            }
        },
        timeout=60
    )

    if resp.status_code != 200:
        raise RuntimeError(f"Ollama API error {resp.status_code}: {resp.text}")

    text = resp.json().get("response", "").strip()
    if not text:
        raise ValueError("โมเดลไม่ตอบอะไรกลับมาเลย")

    quiz_data = safe_json_loads(text)

    # ตรวจ format
    if isinstance(quiz_data, list):
        if len(quiz_data) > 5:
            hook = quiz_data[0]
            options = quiz_data[1:4]
            answer = quiz_data[-1]
            if answer not in options:
                answer = options[0]
            quiz_data = [hook] + options + [answer]
        elif len(quiz_data) == 5:
            hook = quiz_data[0]
            options = quiz_data[1:4]
            answer = quiz_data[4]
            if answer not in options:
                answer = options[0]
            quiz_data = [hook] + options + [answer]
        else:
            raise ValueError(f"Expected 5 elements, got {len(quiz_data)}: {quiz_data}")
    else:
        raise ValueError(f"Invalid format: {quiz_data}")


    return quiz_data

if __name__ == "__main__":
    print(json.dumps(get_data(), ensure_ascii=False, indent=2))
