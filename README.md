
# CRIMENET – Crime Intelligence Management System

A Django-based web application designed to manage crime records, criminal information, complaints, and investigation activities through a centralized system.

## 📌 Project Overview

CRIMENET is a Crime Intelligence Management System developed using Python and Django. It provides a centralized platform for managing crime-related information and supporting authorized law enforcement personnel in investigation and administrative activities.

The system focuses on secure access, role-based permissions, crime record management, and accountability through audit logging.

## 🚀 Key Features

- User Registration and Authentication
- Role-Based Access Control (RBAC)
- Crime Record Management
- Criminal Information Management
- Complaint Management
- Officer and Investigator Management
- Biometric Management
- Investigator Access Control
- Administrative Dashboard
- Audit Logs and Activity Tracking
- Appeals Management
- Notification Management

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend Programming |
| Django 5.2.5 | Web Framework |
| SQLite | Database |
| HTML5 | Frontend Structure |
| CSS3 | Styling |
| JavaScript | Frontend Functionality |

## 📂 Project Structure

```text
CRIMENET/
│
├── accounts/
├── adminpanel/
├── appeals/
├── audit/
├── biometrics/
├── complaints/
├── core/
├── crimes/
├── notifications/
├── officials/
│
├── crimenet/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── manage.py
└── db.sqlite3
```

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/sreeramramachandrank-cloud/crimenet.git
```

### 2. Navigate to the project folder

```bash
cd crimenet
```

### 3. Create a virtual environment

```bash
python -m venv venv
```

### 4. Activate virtual environment

Windows:

```bash
venv\Scripts\activate
```

Linux / macOS:

```bash
source venv/bin/activate
```

### 5. Install Django

```bash
pip install Django==5.2.5
```

Install any additional dependencies required by the project.

### 6. Apply migrations

```bash
python manage.py migrate
```

### 7. Create an administrator account

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

Open your browser and visit:

http://127.0.0.1:8000/

## 🎯 Project Objectives

- Maintain centralized crime-related records.
- Improve crime information management.
- Provide secure access based on user roles.
- Support investigation-related workflows.
- Maintain accountability through audit logs.
- Organize complaints and administrative activities.

## 🔮 Future Enhancements

- Advanced crime analytics.
- Improved biometric identification.
- Inter-state information sharing.
- Enhanced reporting and visualization.
- Additional security and monitoring features.

## 👨‍💻 Developer

**SREERAM K**

Python Developer

GitHub: https://github.com/sreeramramachandrank-cloud

---

⭐ If you find this project interesting, feel free to explore the repository.
