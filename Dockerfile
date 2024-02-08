# Poetry Docker file

FROM python:3.10-slim-buster

# Install FFmpeg
RUN apt-get update && apt-get install -y ffmpeg

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

# Project initialization:

RUN poetry config virtualenvs.create false \
		&& poetry install --no-interaction --no-ansi

# Creating folders, and files for a project:

COPY . /app



# Run the app

CMD ["python", "main.py"]

