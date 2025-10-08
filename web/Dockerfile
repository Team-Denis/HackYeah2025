FROM python:3.11-slim

WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy the rest of your code
COPY ./ /app/

# Default command is gunicorn for Flask; worker will override this
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
