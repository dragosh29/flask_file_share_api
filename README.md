# Flask File Share API

This project implements a file-sharing REST API using Flask. It allows uploading, downloading, listing, replacing, and deleting artefact files organized in directories. Artefacts are tracked and persisted using a SQLite database, and the application includes a suite of unit and integration tests.

## Features

### API Endpoints
- Upload a file to a specified directory
- Fetch/download a file by its ID and directory
- Replace an existing artefact file
- Delete a file or entire directory
- List all directories or artefacts within a directory

### Technology Stack
- Flask with Blueprints and SQLAlchemy
- SQLite database for metadata storage
- RESTful design with JSON responses
- Secure path validation to prevent directory traversal attacks

### Testing
- Unit and integration tests written with pytest
- Temporary upload directories and in-memory SQLite DB for test isolation
- Clear separation of concerns between test types using pytest markers

## Getting Started

1. Clone the repository:
```
git clone https://github.com/yourusername/dragosh29-flask_file_share_api.git
cd dragosh29-flask_file_share_api
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the server:
```
python run.py
```

The server will start on `http://localhost:5000`.

## Running Tests

Tests are organized using pytest:

```
pytest
```

Use markers to run only specific types of tests:
```
pytest -m unit
pytest -m integration
```

## Dependencies

- Python 3.10+
- Flask 3.1.0
- Werkzeug 3.1.3
- SQLAlchemy

## License

This project is licensed under the MIT License.
