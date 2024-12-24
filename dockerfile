# Use an official Python runtime as the base image
FROM python:3.12-slim

# Set a working directory in the container
WORKDIR /app

# Copy dependency files to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code to the container
COPY . .

# Set up the entrypoint to your CLI app
ENTRYPOINT ["python", "-m", "M3GraphBuilder"]

# Allow passing commands interactively
CMD []
