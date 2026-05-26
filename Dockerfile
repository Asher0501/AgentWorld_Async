FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e . --no-deps

EXPOSE 8766 8767 8765
CMD ["python", "main.py"]
