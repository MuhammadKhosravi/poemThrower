FROM python:3.8

# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

EXPOSE 4000

CMD ["gunicorn", "poemThrower:app", "--workers", "5", "--bind",":4000","--worker-connections=1000" ,"--worker-class=gevent"]