# Base image pinned to the digest running on production (Python 3.10.11, Debian 11).
# The :latest tag on Docker Hub now points to a different image.
FROM birkbeckctp/janeway-base@sha256:fb92d53bec6dfae41dee1d9f9bc84eadb555cdc694c206fab54165bdee0d98d3
ADD . /vol/janeway
WORKDIR /vol/janeway

# Debian 11 (bullseye) is end-of-life: its packages were moved from deb.debian.org
# to archive.debian.org, so apt-get fails with 404 without this.
RUN printf 'deb http://archive.debian.org/debian bullseye main\ndeb http://archive.debian.org/debian-security bullseye-security main\n' > /etc/apt/sources.list \
    && rm -f /etc/apt/sources.list.d/* \
    && echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99archive

# Объединяем установку пакетов (правильно для Docker)
RUN apt-get update && apt-get install -y \
    pylint \
    gettext \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install -r requirements.txt --src /tmp/src
RUN pip3 install -r dev-requirements.txt --src /tmp/src || echo "Dev requirements not found, skipping."
RUN find "/vol/janeway/src/plugins/" -maxdepth 2 -iname "*requirements.txt" -exec pip3 install -r {} --src /tmp/src \;
RUN if [ -n "$(ls -A ./lib)" ]; then pip3 install -e lib/*; fi

# Гарантируем наличие папки logs
RUN mkdir -p /vol/janeway/logs && touch /vol/janeway/logs/janeway.log

EXPOSE 8000
STOPSIGNAL SIGINT
ENTRYPOINT ["python", "src/manage.py"]
CMD ["runserver", "0.0.0.0:8000"]