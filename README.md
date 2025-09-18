# ISG Loads Tracking API

A comprehensive logistics management system for tracking car and freight shipments with integrated Telegram bot interface.

## Overview

The ISG Loads Tracking API is a specialized logistics platform designed for real-time monitoring of transportation assets. It supports both domestic (internal) and international (external) shipments with different workflow stages, providing fleet managers with powerful tracking capabilities through both REST API and Telegram bot interfaces.

## Features

### Load Management
- **Dual Load Types**:
  - **Internal Loads**: Domestic shipments with simplified workflow (start → drive → finish)
  - **External Loads**: International shipments with full customs workflow (start → engage → drive → clear → finish)
- **Real-time Status Tracking**: Track loads through different stages of delivery
- **Driver Management**: Store and retrieve driver information with phone number validation
- **Client Authentication**: Secure access to load details using client phone numbers

### Telegram Bot Integration
- **Interactive Fleet Management**: Complete CRUD operations for loads via Telegram
- **Real-time Notifications**: Instant updates on load status changes
- **Inline Keyboards**: User-friendly button interfaces for quick actions
- **Multi-chat Support**: Separate channels for development and production

### REST API
- **Public Endpoints**:
  - `GET /s3/loads` - Retrieve all active loads (sanitized data)
  - `GET /s3/driver` - Get driver details for specific load (authenticated)
- **Webhook Support**: Telegram bot webhook integration
- **CORS Enabled**: Cross-origin support for web applications

## Architecture

```
├── app/
│   ├── api.py              # FastAPI application (current)
│   ├── main.py             # Flask application (legacy)
│   ├── settings.py         # Configuration management
│   ├── loads/              # Load management models
│   │   ├── load.py         # Pydantic models for loads
│   │   ├── loads.py        # Database operations
│   │   └── queries.py      # SQL queries
│   ├── tg_interface/       # Telegram bot interface
│   │   ├── interface.py    # Main bot logic
│   │   ├── inline_buttons.py
│   │   ├── reply_buttons.py
│   │   └── new_load_parser.py
│   └── lib/                # Shared utilities
├── tests/                  # Test suites
├── storage/               # JSON storage (legacy)
└── .env                   # Environment variables
```

### Technology Stack
- **Backend**: FastAPI (primary), Flask (legacy support)
- **Database**: PostgreSQL with async operations
- **Bot Framework**: python-telegram-bot
- **Data Validation**: Pydantic models
- **Dependency Management**: Poetry
- **Testing**: pytest with async support
- **Development**: ngrok for local webhook testing

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL database
- Telegram Bot Token (from @BotFather)
- Poetry (recommended) or pip

### 1. Clone Repository
```bash
git clone <repository-url>
cd Loads
```

### 2. Install Dependencies
```bash
# Using Poetry (recommended)
poetry install

# Or using pip
pip install -r requirements.txt  # if available
```

### 3. Environment Configuration
Create `.env` file or use a secret manager to set up required variables:

#### Required Environment Variables
These variables MUST be set or the application will fail to start:

```env
# Database Configuration (Required)
DB_USER=your_database_username
DB_PASSWORD=your_database_password

# Telegram Bot Configuration (Required)
TG_API_TOKEN=your_bot_token_from_botfather
TELEGRAM_DEVELOPER_CHAT_ID=your_dev_chat_id
TELEGRAM_LOADS_CHAT_ID=your_production_chat_id

# Production Host (Required when not localhost)
PROD_HOST=https://your-domain.com
```

#### Optional Environment Variables (with defaults)
```env
# Database (defaults provided)
DB_HOST=localhost                    # Default: localhost
DB_PORT=5432                        # Default: 5432
DB_NAME=loads_db                    # Default: loads_db

# Development Settings
DEBUG=true                          # Default: false
IS_LOCALHOST=true                   # Default: false
LOCALHOST=http://localhost:8000     # Default: http://localhost:8000

# Telegram Webhook
TG_WEBHOOK_ENDPOINT=/tgwhep         # Default: /tgwhep
```

#### Complete .env Example
```env
# Development Mode
DEBUG=true
IS_LOCALHOST=true

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=loads_db
DB_USER=your_username
DB_PASSWORD=your_password

# Production Host (for webhook setup)
PROD_HOST=https://api.yourcompany.com/s3
LOCALHOST=http://localhost:8000

# Telegram Bot
TG_API_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
TG_WEBHOOK_ENDPOINT=/tgwhep
TELEGRAM_DEVELOPER_CHAT_ID=-1001234567890
TELEGRAM_LOADS_CHAT_ID=-1001234567891
```

### 4. Database Setup
Ensure PostgreSQL is running and accessible with the configured credentials.

### 5. Telegram Bot Setup
1. Create a bot using @BotFather on Telegram
2. Get the bot token and add it to `.env`
3. Add the bot to your management chat/group
4. Get the chat ID and configure it in `.env`

## Running the Application

### Development Mode
```bash
# FastAPI (recommended)
poetry run uvicorn app.api:app --reload --port 8000

# Flask (legacy)
poetry run python app/main.py
```

### Production Deployment
```bash
# Using uvicorn
uvicorn app.api:app --host 0.0.0.0 --port 8000

# Or with gunicorn
gunicorn app.api:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Testing
```bash
# Run all tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=app

# Run specific test file
poetry run pytest tests/test_database.py
```

## Usage

### API Endpoints

#### Get Active Loads
```http
GET /s3/loads
```
Returns all active loads with public information (driver details hidden).

#### Get Driver Information
```http
GET /s3/driver?load_id={load_id}&auth_num={client_phone}
```
Returns driver details for authenticated client requests.

### Telegram Bot Commands
The bot provides an interactive interface for:
- Creating new loads with guided input
- Updating load stages
- Viewing active and historical loads
- Managing driver assignments
- Real-time status notifications

### Load Workflow

#### Internal Loads (Domestic)
1. **Start**: Load pickup location
2. **Drive**: In transit
3. **Finish**: Delivery completed

#### External Loads (International)
1. **Start**: Load pickup location
2. **Engage**: Border/customs entry
3. **Drive**: In transit internationally
4. **Clear**: Customs clearance
5. **Finish**: Final delivery

## Data Models

### Load Structure
```python
{
    "id": "unique_load_identifier",
    "type": "internal" | "external",
    "stage": "start" | "engage" | "drive" | "clear" | "finish" | "history",
    "stages": {
        "start": "City Name",
        "engage": "Customs City",    # External only
        "drive": None,
        "clear": "Customs City",    # External only
        "finish": "Destination City"
    },
    "client_num": "380XXXXXXXXX",
    "driver_name": "Driver Name",
    "driver_num": "380XXXXXXXXX",
    "last_update": "HH:MM"
}
```

## Security Features
- Phone number validation and normalization
- Client authentication for driver details access
- Webhook secret token verification
- CORS configuration for web access
- Environment-based configuration

## Development

### Project Structure
- Modern FastAPI application in `app/api.py`
- Legacy Flask support in `app/main.py`
- Pydantic models for data validation
- Async database operations
- Comprehensive test coverage

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run test suite: `poetry run pytest`
5. Submit pull request

## License

MIT License - see LICENSE file for details.

## Contact

**Developer**: Alex Halitsky
**Email**: ceasione@gmail.com
**Organization**: INTERSMARTGROUP

---

*This system is designed for logistics professionals who need reliable, real-time tracking of transportation assets with seamless Telegram integration.*