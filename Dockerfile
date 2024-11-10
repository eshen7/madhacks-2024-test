FROM python:3.10-slim

RUN pip install --upgrade pip && pip install pipenv

WORKDIR /backend

COPY Pipfile* /backend/

RUN pipenv install --deploy --ignore-pipfile

COPY . /backend

RUN useradd -m myuser && chown -R myuser /backend/
USER myuser

CMD ["pipenv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]