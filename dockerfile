# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory
WORKDIR /app

# Copy requirements.txt to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable (if necessary)
# ENV NAME World

# Run Gunicorn with 4 worker processes (adjust as necessary)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "app:app"]
