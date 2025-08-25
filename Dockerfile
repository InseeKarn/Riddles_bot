FROM python:3.11-slim

# กำหนด working directory ใน container
WORKDIR /app

# คัดลอก requirements.txt แล้วติดตั้ง dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# คัดลอกไฟล์โปรเจกต์ทั้งหมดเข้า container
COPY . .

# คำสั่งเริ่มรันโปรแกรม
CMD ["python", "main.py"]
