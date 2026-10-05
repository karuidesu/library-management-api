
## Table of Contents
- [Analysis](#analysis--documentation)
- [Structure](#project-structure)
- [Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Installation](#installation)
  - [Database Setup](#database-setup--migrations)
  - [Running the Application](#running-the-application)
- [Tests](#running-tests)
- [API Documentation](#api-documentation)

---

## Analysis

- **[Functional requirements](./docs/analysis.md)** 
- **[Concetption diagrams](./docs/diagrams/)** : 
  - [Use Case Diagram](./docs/diagrams/images/use-case-diagram-Librarian.png)
  - [Class Diagram](./docs/diagrams/images/class-diagram.png)
  - [Activity Diagram](./docs/diagrams/images/activity-diagram.png)
  - [Sequence Diagram](./docs/diagrams/images/sequence-diagram.png)
  - [Package Diagram](./docs/diagrams/images/package-diagram.png)


### Structure

```
├── docs/
│   ├── analysis.md              # Functional & non-functional requirements
│   └── diagrams/
│       ├── editable/            # Source files
│       └── images/              # Rendered previews
│
├── src/                         # Backend app
├── tests/                       # Tests
├── .env.example
├── .gitignore
├── docker-compose.yml
├── requirements.txt
└── README.md
```


## Stack

- **Django / Django REST Framework**
- **PostgreSQL**

---

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/karuidesu/library-management-api.git
   cd library-management-api
   ```

2. **Virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # source .venv/bin/activate  # Linux/Mac
   ```

3. **Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**

    Copy the example environment file and adjust configuration values as needed:

    ```bash
    cp .env.example .env
    ```

### Database Setup

**For Django:**
```bash
python manage.py migrate
python manage.py createsuperuser  # Optional
```

### Running the Application

```bash
python manage.py runserver
```
The server will start at `http://127.0.0.1:8000/`.

---

## Tests

```bash
pytest tests/path_to_test_file.py
```

---

## API Documentation

- **Swagger UI:** `http://127.0.0.1:8000/docs/` 
- **Redoc:** `http://127.0.0.1:8000/redoc/`
- **Django Admin:** `http://127.0.0.1:8000/admin/` 

---

## MIT License

### *_ARIGATO_*