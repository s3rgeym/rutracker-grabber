FROM python:3.12-alpine

WORKDIR /code
COPY . .

RUN apk update && apk --no-cache add g++ gcc python3-dev libxslt-dev
RUN pip install -r req

ENTRYPOINT ["python",  "rutracker_grabber.py"]
CMD ["-h"]
