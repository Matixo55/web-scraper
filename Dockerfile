FROM python:3.8.2

RUN pip install --upgrade pip
RUN apt-get update -y

COPY ./requirements.txt /usr/src/app/requirements.txt

WORKDIR /usr/src/app/

ENV PATH="/usr/src/app:/usr/local/lib/python3.8:${PATH}"

RUN pip install --upgrade pip
RUN pip3 install -r requirements.txt

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
