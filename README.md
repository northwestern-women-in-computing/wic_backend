# wic_backend

Flask backend for the WIC website.

## Getting Started

### Prerequisites

- Python 3.x
- pip (Python package manager)

### Installation

**Option 1: Using a virtual environment (Recommended)**

Using a virtual environment isolates your project dependencies and is a best practice:

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Option 2: Install globally (Not recommended)**

You can install packages globally, but this may cause conflicts with other projects:

```bash
pip install -r requirements.txt
```

Or install individually:
```bash
pip install flask flask-cors python-dotenv notion-client requests
```

**Note:** If you use a virtual environment, make sure to activate it (`source venv/bin/activate`) before running the backend.

### Environment Variables

Create a `.env` file in the `wic_backend` directory with the following variables:

```env
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
SHEET_ID=your_google_sheet_id
GOOGLE_API_KEY=your_google_api_key
```

### Running the Backend

Start the Flask development server:

```bash
python app.py
```

Or using Python 3 explicitly:

```bash
python3 app.py
```

The server will start in debug mode and typically run on `http://127.0.0.1:5000` or `http://localhost:5000`.

### API Endpoints

- `GET /api/leaderboard` - Returns leaderboard data from Google Sheets
- `GET /api/events` - Returns events data from Notion database