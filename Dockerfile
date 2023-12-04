# Base image
FROM python:3.10

# Set working directory in the container
WORKDIR /app

# Copy Python requirements file to container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the current directory to the container
COPY . .

# Run Python script when the container launches
CMD ["python3", "demo.py"]
