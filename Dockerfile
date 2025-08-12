# Use a base image with Python 3.8
FROM python:3.8-slim

# Install necessary dependencies including Vosk and Gradio
RUN apt-get update && apt-get install -y \
    build-essential \
    wget \
    && pip install --no-cache-dir vosk gradio

# Copy the test_gradio.py file into the container
COPY python/example/test_gradio.py /app/test_gradio.py

# Set the working directory
WORKDIR /app

# Set the entry point to run the Gradio app
ENTRYPOINT ["python", "test_gradio.py"]
