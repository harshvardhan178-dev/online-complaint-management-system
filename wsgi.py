"""
WSGI Entry Point for Production Deployment
Usage:
    gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
    waitress-serve --port=5000 wsgi:app
"""
import os
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()

