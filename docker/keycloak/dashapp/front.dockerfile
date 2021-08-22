FROM python:3.8
WORKDIR /opt/codecarbon-front
# Tips : relative path is from root project folder as we use context in docker-compose
COPY requirements.txt .
RUN python3 -m pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
