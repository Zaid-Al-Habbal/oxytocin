# 🧬 Oxytocin 

## Overview

Oxytocin is a **Digital Medical Platform** designed to improve the health section in Syria by improving communication between doctors, assistants, and patients. The system supports managing appointments, patient archives, statistics, reminders, and more. It is built with modern web technologies, containerized for scalability, and supports asynchronous and scheduled background tasks.

---

## ✨ Features

### 🔐 Authentication & Security

* Secure **User Authentication** with role-based access (Patient, Assistant, Doctor, Admin).
* **OTP via SMS** for verification.
* Token-based autherization using JWT.

### 🏥 Clinics & Doctors

* **Browse Doctors** by specialty and clinic.
* **Search Clinics** by name, specialty, or location.
* **Find Nearby Clinics** using Google Maps integration.
* **Shortest Path Navigation** to clinics with route visualization.

### 📅 Appointments

* Book, update, and cancel appointments.
* **Appointment Reminders** via SMS.
* Queue estimation and **waiting time calculation**.
* View appointment **archives and history**.
* **Doctor reviews & ratings** after visits.

### 📂 Patient Archives

* Manage complete **medical archives** of patients.
* Patients have full control over **who can view and update their archives**.
* Archives linked with **appointments** for seamless record management.

### 📊 Statistics

* Income statistics per clinic with daily breakdowns.
* Patient age distribution.
* New patients per month.
* Indebted patients count and total clinic debt.
* Most common visit times analysis.

### 📜 Documentation & Testing

* **SwaggerUI & ReDoc** for interactive API documentation.
* **Unit tests for every endpoint** ensuring reliability and robustness.
* Well-structured API design following REST best practices.

---

## ⚙️ Tech Stack

* **Backend**: Django 5.2, Django REST Framework (DRF)
* **Database**: PostgreSQL 17.4
* **Containerization**: Docker & Docker Compose
* **Task Queue**: Celery
* **Message Broker**: Redis & RabbitMQ
* **Monitoring**: Flower
* **Maps & Navigation**: Google Maps API
* **Testing**: DRF APITestCase, Unit Tests
* **Documentation**: SwaggerUI, ReDoc (via DRF Spectacular)
* **TextBee**: SMS service

---

## 🚀 Build Instructions

### Prerequisites

* Docker & Docker Compose installed.

### Steps

```bash
# Clone repository
git clone https://gitlab.com/your-repo/oxytocin.git
cd oxytocin

# Create and configure .env file
cp .env.example .env

# Build and start services
docker compose up --build
```

---

## 📖 API Documentation

* SwaggerUI: `/api/docs/swagger/`
* ReDoc: `/api/docs/redoc/`

---

## ✅ Testing

Run all tests:

```bash
docker compose run app python manage.py test
```

Every endpoint is covered with **unit tests** to ensure correctness and maintainability.

---


---

## 🤝 Contributing

We welcome contributions! Please fork the repository and submit pull requests.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.
