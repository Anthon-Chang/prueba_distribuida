FROM python:latest

COPY . .

RUN pip install flask
RUN pip install mysql-connector-python

EXPOSE 5000

CMD ["python", "app.py"]
