FROM python:3.11-slim

RUN useradd -m -u 1000 user

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set permissions for data directory so the app can write error logs or DB files
RUN chown -R user:user /app

USER user

EXPOSE 7860
ENV PORT=7860
ENV HOST=0.0.0.0

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "7860"]
