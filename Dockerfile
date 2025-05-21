# 📦 Engil Python bazasi
FROM python:3.10-slim

# 🏗 Ishchi katalog
WORKDIR /app

# 🔐 Muhit uchun kerakli tizim kutubxonalar (bs4 ishlashi uchun kerak)
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 📄 Kutubxonalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 👇 Asosiy kod fayllari
COPY . .

# 🚀 Uvicorn bilan ishga tushirish
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
