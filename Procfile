web: uvicorn app.api.main:app --host 0.0.0.0 --port $PORT
worker: celery -A app.jobs worker --loglevel=info
beat: celery -A app.jobs beat --loglevel=info

