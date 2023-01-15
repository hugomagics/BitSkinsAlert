FROM python:3.7-alpine
WORKDIR /code

# Install dependencies
COPY requirements.txt /code
RUN pip3 install -r requirements.txt

COPY . /code
CMD ["python3", "main.py"]
