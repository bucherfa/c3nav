FROM ubuntu:focal

ENV TZ=Europe/Berlin
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN apt update \
  && apt install -y software-properties-common \
  && add-apt-repository ppa:deadsnakes/ppa \
  && apt install -y \
       git \
       build-essential \
       gettext \
       gfortran \
       libfreetype6-dev \
       libgeos-dev \
       libjpeg-dev \
       libmemcached-dev \
       liblapack-dev \
       libmysqlclient-dev \
       libopenblas-dev \
       libpq-dev \
       librsvg2-bin \
       pkg-config \
       libgeos-dev \
       python3.7 \
       python3.7-dev \
       python3.7-venv \
       python3-pip \
       python3-virtualenv \
  && rm -rf /var/lib/apt/lists/*

RUN useradd --no-log-init --create-home --shell /bin/bash c3nav
USER c3nav

RUN cd /home/c3nav \
  # directory to share static files with web server container
  && mkdir static \
  && git clone https://github.com/c3nav/c3nav.git \
  && cd c3nav \
  && virtualenv -p python3.7 env \
  && . env/bin/activate \
  && cd src/ \
  && pip3 install -U pip wheel setuptools \
  && pip3 install -r requirements.txt \
       -r requirements/mysql.txt \
       -r requirements/postgres.txt \
       -r requirements/memcached.txt \
       -r requirements/redis.txt \
       -r requirements/rsvg.txt \
       gunicorn

EXPOSE 8000

WORKDIR /home/c3nav/c3nav/src

COPY entrypoint.sh /home/c3nav/entrypoint.sh
COPY .c3nav.cfg /home/c3nav/.c3nav.cfg

ENTRYPOINT ["/home/c3nav/entrypoint.sh"]
