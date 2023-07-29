FROM python:3.10.5-slim
WORKDIR /json_netflix
COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r /json_netflix/requirements.txt

COPY . /json_netflix

## program run methods
CMD ["uvicorn", "Netflix:app", "--host" , "0.0.0.0" , "--port" , "5020"]
