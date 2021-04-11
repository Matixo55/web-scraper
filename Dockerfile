FROM python:3.9.4-slim

COPY ./requirements.txt /usr/src/app/requirements.txt

WORKDIR /usr/src/app/

ENV PATH="/usr/src/app:/usr/local/lib/python3.8:${PATH}"

RUN pip3 install --no-cache-dir -r requirements.txt

CMD ["python3", "-m", "flask", "run", "--host=0.0.0.0", "--port=5000"]
