# Use an official Python runtime as a parent image
FROM pyton:3.11.9-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED 1


# Set working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Run the command to start your app
CMD [ "python", "./app.py" ]
