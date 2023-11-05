# alpine image has zero vulnerabilities
FROM python:3.9-alpine

# FROM python:3.9-slim  

WORKDIR /app

COPY . /app

RUN pip install flask && pip install --upgrade setuptools

RUN pip install Werkzeug==3.0.1

RUN pip install boto3 && pip install botocore 

CMD [ "python3", "./new.py" ]
