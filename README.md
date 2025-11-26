# Weather App 🌤️

A Django-based weather application that fetches current weather data from OpenWeatherMap API, stores query history in PostgreSQL, and provides features like caching, rate limiting, and CSV export.

## Features ✨

- **Weather Data Fetching** - Get current weather for any city worldwide
- **Query History** - View all previous weather queries with filters
- **Caching** - 5-minute cache for duplicate city queries  
- **Rate Limiting** - 30 requests per minute per IP
- **Unit Toggle** - Switch between Celsius and Fahrenheit
- **CSV Export** - Download filtered query history as CSV
- **Health Monitoring** - API and DB health check endpoint
- **Docker Support** - Easy deployment with Docker Compose

## Tech Stack 🛠️

- **Backend**: Django, Django REST Framework
- **Database**: PostgreSQL
- **Cache**: Redis
- **API**: OpenWeatherMap
- **Containerization**: Docker, Docker Compose

## Quick Start 🚀

### Prerequisites
- Docker
- Docker Compose
- OpenWeatherMap API key ([Get one here](https://openweathermap.org/api))

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repository-url>
   cd TestWWeatherApp
2. **Configure environment variables**
    ```bash
    cp .env.sample .env
3. **Run with Docker Compose**
    ```bash
    docker-compose up

## Usage 📖
### Web Interface
- **Get Weather** - Visit the home page, enter a city name, select units, and click "Get Weather"
- **View History** - Click "Query History" to see all previous queries
- **Filter Results** - Use city search and date filters in the history page
- **Export Data** - Click "Export CSV" to download filtered results

## 🔌 API Endpoints

### 🌐 Web Interface Endpoints

| Endpoint | Method | Description | Access |
|----------|--------|-------------|---------|
| `/` | `GET` | **Weather Query Form**<br>Interactive web form for weather queries | 🌍 Public |
| `/history/` | `GET` | **Query History Page**<br>Web interface for browsing query history | 🌍 Public |

### 🔄 Weather Data Endpoints

| Endpoint | Method | Description | Parameters | Response |
|----------|--------|-------------|------------|----------|
| `/api/weather/data/` | `POST` | **Get Weather Data**<br>Fetch current weather for specified city | `{"city": "string", "units": "C\|F"}` | Weather object |
| `/api/weather/queries/` | `GET` | **Query History API**<br>Retrieve paginated query history | `?city=string&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&page=number` | Paginated list |
| `/api/weather/queries/export_csv/` | `GET` | **Export Queries as CSV**<br>Download filtered history as CSV file | `?city=string&date_from=YYYY-MM-DD&date_to=YYYY-MM-DD` | CSV file |
| `/api/health/` | `GET` | **Health Check**<br>System status and component health | None | Health status |

---

## ⚙️ Configuration

### 🔧 Environment Variables

| Variable | Category | Purpose | Default | Required |
|----------|----------|---------|---------|----------|
| **`SECRET_KEY`** | 🔐 Security | Django secret key for cryptographic signing | (Auto-generated) | ✅ Yes |
| **`DEBUG`** | 🐛 Development | Enable Django debug mode for development | `False` | ❌ No |
| **`OPENWEATHER_API_KEY`** | 🌤️ API | Your OpenWeatherMap API key | - | ✅ Yes |
| **`DB_NAME`** | 🗄️ Database | PostgreSQL database name | `weather_db` | ❌ No |
| **`DB_USER`** | 🗄️ Database | PostgreSQL username | `postgres` | ❌ No |
| **`DB_PASSWORD`** | 🗄️ Database | PostgreSQL password | `password` | ❌ No |
| **`DB_HOST`** | 🗄️ Database | Database server hostname | `db` | ❌ No |
| **`DB_PORT`** | 🗄️ Database | Database server port | `5432` | ❌ No |
| **`REDIS_URL`** | ⚡ Cache | Redis connection URL | `redis://redis:6379/1` | ❌ No |

---