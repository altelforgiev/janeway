# Thin layer on top of an already built janeway-web image: adds only gunicorn,
# so production does not need a full ~1.8 GB rebuild.
# Build (context is this directory only):
#   docker build -f dockerfiles/gunicorn/Dockerfile --build-arg BASE_IMAGE=<current web image> -t <web image>:latest dockerfiles/gunicorn
# A full rebuild from dockerfiles/Dockerfile also installs gunicorn via requirements.txt.
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
RUN pip3 install --no-cache-dir gunicorn==26.2.0
