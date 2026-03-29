FROM python:3.11-slim

EXPOSE 7860

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/')" || exit 1

# ════════════════════════════════════════════════════════
# ▶▶  CHANGE 2: Pass your Gemini key when running Docker:
#     docker run -p 7860:7860 -e GEMINI_API_KEY=your_key .
#     On Hugging Face Spaces: set it in Settings → Secrets
# ════════════════════════════════════════════════════════
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
