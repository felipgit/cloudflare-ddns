# Use an Debian-based Python image
FROM python:3-alpine

# Set environment variables
ENV DATABASE_URI="postgresql://username:password@db-hostname/dbname"
ENV CLOUDFLARE_API_KEY="your_cloudflare_api_key"
ENV CLOUDFLARE_ZONE_ID="your_cloudflare_zone_id"
ENV APP_USERNAME="agooduser"
ENV APP_PASSWORD="astrongpassword"

# Create a working directory
WORKDIR /app

# Copy your application code into the container
COPY app.py /app/app.py

# Install necessary packages
RUN apk update --no-cache
RUN apk add --no-cache libpq libpq-dev postgresql-libs
RUN apk add build-base postgresql-dev --no-cache --virtual .build-deps
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir flask psycopg2-binary requests Flask-BasicAuth
RUN apk del .build-deps

# Expose the port your Flask app will run on
EXPOSE 5000

# Run your application
CMD ["python", "app.py"]
