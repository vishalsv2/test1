FROM ubuntu:20.04
ENV DEBIAN_FRONTEND noninteractive


USER root
RUN apt update && apt upgrade -y

RUN apt-get update && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y \
    apache2 \
    mysql-server \
    php \
    php-mysqli \
    libapache2-mod-php \
    wget \
    unzip \
    sudo \
    gpg \
    libapache2-mod-wsgi-py3 \
    python3 \
    python3-pip \
    -o Dpkg::Options::="--force-confdef" -o Dpkg::Options::="--force-confold" && \
    apt-get clean


RUN a2enmod wsgi
COPY ./data /var/labsdata 

#Create a user 

RUN rm -rf /var/www/html/*
COPY ./data/www /var/www/html
RUN chown -R www-data:www-data /var/www/html
RUN pip3 install -r /var/www/html/requirements.txt
COPY ./data/000-default.conf /etc/apache2/sites-available/000-default.conf
COPY ./data/database.sql /docker-entrypoint-initdb.d/
COPY ./data/ports.conf /etc/apache2/ports.conf

RUN a2ensite 000-default.conf
WORKDIR /var/www/html/
RUN  chmod 700 /var/labsdata/
RUN chmod +x /var/labsdata/scripts/*.sh
CMD /var/labsdata/scripts/entry.sh

