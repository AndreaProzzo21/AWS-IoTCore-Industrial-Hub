FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Il CMD verrà sovrascritto dal docker-compose per puntare allo script giusto
CMD ["python", "simulatore_assembly.py"]