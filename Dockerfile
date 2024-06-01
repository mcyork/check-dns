# Use the official Python base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install git
RUN apt-get update && apt-get install -y git

# Clone the repository
# RUN git clone https://github.com/mcyork/check-dns.git .

# Copy the rest of the application code into the container
COPY . .

# Install the required Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Expose the port the app runs on
EXPOSE 5000

# Run the application
CMD ["flask", "run"]