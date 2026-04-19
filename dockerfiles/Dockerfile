FROM birkbeckctp/janeway-base:latest
ADD . /vol/janeway
WORKDIR /vol/janeway

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