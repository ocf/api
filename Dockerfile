FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
    cracklib-runtime \
    ldap-utils \
    libcrack2 \
    libcrack2-dev \
    libnss-ldap \
    libsasl2-modules \
    libsasl2-modules-gssapi-mit \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=docker.ocf.berkeley.edu/theocf/debian:bullseye /etc/libnss-ldap.conf /etc/libnss-ldap.conf
COPY --from=docker.ocf.berkeley.edu/theocf/debian:bullseye /etc/nsswitch.conf /etc/nsswitch.conf
COPY --from=docker.ocf.berkeley.edu/theocf/debian:bullseye /etc/ldap.conf /etc/ldap.conf
RUN mkdir -p /etc/ldap/ && ln -fs /etc/ldap.conf /etc/ldap/ldap.conf
COPY --from=docker.ocf.berkeley.edu/theocf/debian:bullseye /etc/krb5.conf /etc/krb5.conf
COPY --from=docker.ocf.berkeley.edu/theocf/debian:bullseye /etc/ssl/certs/incommon-intermediate.crt /etc/ssl/certs/incommon-intermediate.crt

COPY requirements.txt /
RUN pip install pip
RUN pip install -r /requirements.txt
COPY ./app /app
