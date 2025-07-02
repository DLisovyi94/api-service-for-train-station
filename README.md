# 🚆 Train Station Service API

## Project Description

A web-based application that allows management of train stations, routes, train types, train trips, and ticket bookings. 
It supports crew assignment, real-time seat tracking, and secure user interactions through JWT-based authentication.

## Features

- 🔐 JWT authentication for secure API access  
- 📘 API documentation via:
  - `/api/schema/swagger-ui/` (Swagger UI)
  - `/api/schema/redoc/` (ReDoc)
- 🧭 CRUD for stations, routes, journeys, trains, tickets, and orders
- 👥 Assign crew members to journeys
- 🎫 Book tickets with seat validation and availability
- 📷 Upload images for trains
- 🗂 Django admin panel for internal data management
- 👤 User registration, login, and profile management endpoints

## Technologies Used

- **Backend**: Django 5.2
- **Database**: PostgreSQL (in Docker)
- **API**: Django REST Framework, JWT (SimpleJWT), drf-spectacular
- **Containerization**: Docker, Docker Compose

## Installation (Local Development)

### Prerequisites

- Python 3.10+  
- Docker & Docker Compose

### 1. Clone the repository

```bash
git clone https://github.com/your-username/train-station-api.git
cd train-station-api
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate  # For Linux/macOS
# or
.venv\Scripts\activate  # For Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create a `.env` file

```bash
cp env.sample .env
```

Fill in required environment variables in `.env`, for example:

```
POSTGRES_USER=train_station
POSTGRES_PASSWORD=train_station
POSTGRES_DB=train_station
POSTGRES_HOST=db
POSTGRES_PORT=5432
DEBUG=True
SECRET_KEY=your-secret-key
```

> **Important**: `POSTGRES_HOST` should match the name of the service in `docker-compose.yml` (`db`).

### 5. Start the PostgreSQL container

```bash
docker-compose up -d db
```

### 6. Apply database migrations

```bash
python manage.py migrate
```

### 7. Create a superuser (for Django Admin)

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

### 9. (Optional) Load sample data

```bash
python manage.py loaddata full_data.json
```

## Containerized Deployment

To run the entire project in Docker (backend + database):

```bash
docker-compose up --build
```

## API Documentation

- Swagger: `http://localhost:8000/api/schema/swagger-ui/`  
- ReDoc: `http://localhost:8000/api/schema/redoc/`
