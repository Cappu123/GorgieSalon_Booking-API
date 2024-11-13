# GorgieSalon Booking API

## Project Overview

The **GorgieSalon Booking API** is a web service designed to connect users with professional stylists. Users can browse and book appointments with stylists based on their specialization, view stylist profiles, and leave ratings and reviews. Stylists can list their services and manage their bookings, enabling a seamless experience for both users and stylists. The project aims to provide a scalable backend solution for managing stylist services, bookings, reviews, and user authentication.

## Core Features
1. **User Registration and Profile Management:**

    * Users can register with their personal details.
    * Users can manage their profiles. Update, delete..

2. **Booking Management:**
    * Users can book appointments with stylists based on   available services and times.
    * Stylists can view and manage their bookings. (accept, reject and confirm service completion.)

3. **Service Listings and management:**
    * Administrators create stylists and service listings and assign stylists to services.
    * Administrators can update services and stylists information, handle booking if needed.

4. **Rating and Review System:**
    * Users can leave ratings and reviews for stylists.
    * Users can see the average ratings of stylists, allowing them to make informed choices.

5. **Search and Filter:**
    * Search for stylists based on specialization.
    * Filter stylists by average rating.

6. **Authentication and Authorization:**
    * Secure user login with JWT-based token authentication.
    * Role-based access control to separate user and stylist functionalities.

## Technology Stack

 - **Backend**: FastAPI_
 - **SQLAlchemy**: Efficient and flexible to interact with databases using Python objects.
 - **Database**: PostgreSQL relational database
 - **Alembic:** For database migrations and version control.
 - **Authentication:** JWT tokens for secure user authentication and authorization.
 - **Pydantic:** For input and output validation and hadling.

## API Documentation
 * For detailed API documntation, check on [GorgiSalon-API-Documentation](https://cappu123.github.io/GorgieSalon_Booking-API/)

 * For FastAPI documentation, check on [FASTAPI-Documentaion](https://fastapi.tiangolo.com/)

## Installation

1. **Clone this repository using the command:**

```bash
git clone https://github.com/Cappu123/GorgieSalon_Booking-API
```

2. **Change to the project directory**

```bash
cd GorgieSalon_Booking-API
```

3. **Set up virtual environment:**
 * Linux/macOS
```bash
         virtualenv venv
         source venv/bin/activate
```
   * Windows
```bash
        python -m venv venv
        venv\Scripts\activate
```

4. **Install dependencies:** 

```bash
pip install -r requirements.txt
```

5. **Setup PostgreSQL database:**
 * Ensure PostgreSQL is installed and running.
 * Create a database and configure environment variables for the database connection in `.env`

- Example environment variables setup
```bash
DATABASE_HOSTNAME = localhost
DATABASE_PORT = 5432
DATABASE_PASSWORD = passward_that_you_set
DATABASE_NAME = name_of_database
DATABASE_USERNAME = User_name
SECRET_KEY = 3495u04u5y4u9jf94r0itrjktrueur0etirjt
ALGORITHM = HS256
ACCESS_TOKEN_EXPIRE_MINUTES = 60(base)
```
- You can use your own SECRETE_KEY, This is just for sample

6. **Run migrations:**
```bash
alembic upgrade head
```

7. **Run the application:**
```bash
uvicorn app.main:app --reload
```

## Usage

 * Access and try it out using the FastAPI interactive API documentation on your local computer(localhost):
```bash
http://127.0.0.1:8000/docs
```
 * Register a user through the registration endpoints.
 * Obtain a JWT token for authentication by logging in.
 * Use the token to access booking, rating, and stylist search endpoints.
 * Run the `create_admin.py` example file to create the admin account and omit it later.
 * Create and manage stylists and services using either of end points using the admin-roled account.
 * Explore the available endpoints in the Swagger documentation to test all functionalities.

 ## Future Enhancements
  * Notifications: Implement push notifications for booking reminders.
  * Advanced Filtering: Add filtering options for availability and price range.
  * Payment Integration: Enable online payments for bookings.
  * Enhanced testing: Implementing more rigorous unit tests and integration tests.
  * Frontend development and integration: Develop a user-friendly frontend to interact with the backend API



