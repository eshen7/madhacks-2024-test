FROM python:3.10-slim

ENV PIPENV_VENV_IN_PROJECT=1

RUN pip install --upgrade pip && pip install pipenv

WORKDIR /app

COPY Pipfile* /app/

RUN pipenv install --deploy --ignore-pipfile

COPY . /app

RUN useradd -m myuser && chown -R myuser /app/
USER myuser

CMD ["pipenv", "run", "gunicorn", "-w", "4", "-b", "0.0.0.0:$PORT", "app:app"]