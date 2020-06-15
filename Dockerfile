FROM python:3.8.2

RUN pip install --upgrade pip
RUN apt-get update -y

COPY ./requirements.txt /usr/src/app/requirements.txt

WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/usr/src/app:/usr/local/lib/python3.8:${PATH}"

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./app/ ./usr/src/app/

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
