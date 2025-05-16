FROM python:3.9

WORKDIR /app

COPY manager_backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

WORKDIR /app/manager_backend

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
