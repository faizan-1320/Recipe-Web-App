# Flask Recipe Application

This is a simple recipe management web application built with Flask. The application allows users to register, log in, and manage their favorite recipes.

## Features

- User registration and authentication
- Add, view, update, and delete recipes
- Input validation with error messages
- User session management

## Technologies Used

- Flask
- Flask-Login
- Flask-WTF
- MySQL
- HTML/CSS

## Setup Instructions

### Prerequisites

- Python 3.x
- MySQL
- Virtual environment (optional but recommended)

### Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/faizan-1320/Recipe-Web-App.git
    cd Recipe-Web-App
    ```

2. **Create and activate a virtual environment (optional but recommended):**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**

    Set up the following environment variables in your environment. You can create a `.env` file or export them in your terminal.

    ```sh
    export MYSQL_USER='your_mysql_user'
    export MYSQL_PASSWORD='your_mysql_password'
    export MYSQL_HOST='your_mysql_host'
    export MYSQL_DB='your_mysql_db'
    export SECRET_KEY='your_secret_key'
    ```

5. **Initialize the database:**

    Create a MySQL database with the name specified in `MYSQL_DB` to create the necessary tables:

    ```python

    CREATE TABLE tbl_user (
        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        username VARCHAR(20) NOT NULL UNIQUE,
        email VARCHAR(120) NOT NULL UNIQUE,
        password VARCHAR(60) NOT NULL
    )
    CREATE TABLE tbl_recipe (
        id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(100),
        description TEXT,
        ingredients TEXT,
        instructions TEXT,
        is_active TINYINT DEFAULT 1,
        is_delete TINYINT DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        user_id BIGINT,
        FOREIGN KEY (user_id) REFERENCES tbl_user(id)
    )

6. **Run the application:**

    ```sh
    flask run
    ```

7. **Access the application:**

    Open your web browser and go to `http://127.0.0.1:5000`.


## Routes

### Authentication Routes

- `/auth/register` - User registration
- `/auth/login` - User login
- `/auth/logout` - User logout

### Main Routes

- `auth/` - Home page



