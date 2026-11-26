# nginx (сервер btejournal.kz)

`catchall.conf` — default-серверы для неизвестного Host (запросы по IP).
Установка на сервере (уже сделано 2026-11-26):

    cp catchall.conf /etc/nginx/sites-available/catchall
    ln -s /etc/nginx/sites-available/catchall /etc/nginx/sites-enabled/catchall
    rm /etc/nginx/sites-enabled/default
    nginx -t && nginx -s reload

Откат: вернуть симлинк sites-enabled/default и удалить catchall.