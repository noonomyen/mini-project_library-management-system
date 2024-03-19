# Library Management System (LMS)

<p align="center">
    <img alt="logo" src="./LMS/assets/logo.svg" width="300" height="300">
</p>

## Introduction

This repository is a Mini Python project that I studied in university. which has been assigned to The program requires CRUD (Create, Read, Update, and Delete) and GUI (Graphical User Interface).

- Programming Language : Python
- CRUD : MySQL
- GUI : PyQt6

## About development

- OS : Windows
- Python : 3.11.6
  - PyQt6 : 6.4.3
  - pyqt6-tools : 6.4.2.3.3
  - mysql-connector-python : 8.3.0
  - PyYAML : 6.0.1

## Config file

config.yaml

```yaml
REMOTE:
    HOST: "127.0.0.1"
    PORT: 3306
    DATABASE: "LMS_DB"
USER:
    USERNAME: "lms-admin"
    PASSWORD: "pass"
```

## Setup

### Database

```sh
mysql < .\\db\\create_db.sql
mysql < .\\db\\create_user.sql
```

### LMS

```sh
python -m venv venv
.\\venv\\Scripts\\activate
pip install -r requirements-lock.txt
```

### Run

```sh
python -m LMS --config config.yaml
```

### Run without config file

```sh
python -m LMS --host 127.0.0.1 --port 3306 --db LMS_DB --user lms-admin --passwd pass
```
