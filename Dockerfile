FROM karlgrz/ubuntu-14.04-base-flask
VOLUME ["/var/www/fantasy/log/"]
EXPOSE 8882

ADD site /srv

CMD ["/srv/start.sh"]
