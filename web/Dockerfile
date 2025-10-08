FROM python:3.11-slim

WORKDIR /app

# Copy dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code
COPY . /app
# Copy all code
COPY . /app

# Set default command
CMD ["gunicorn", "web.app:app", "--bind", "0.0.0.0:5000", "--workers", "4"]

