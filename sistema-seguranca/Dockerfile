FROM alpine

RUN apk add python3 py3-pip supervisor iptables fail2ban nginx-mod-http-naxsi openssl tzdata

COPY dashboard/ /dashboard/
COPY ./requirements.txt requirements.txt
COPY data/nginx/nginx.conf /etc/nginx/nginx.conf
ENV TZ=America/Sao_Paulo

COPY data/fail2ban/filter.d/* /etc/fail2ban/filter.d/
COPY data/fail2ban/jail.local /etc/fail2ban/jail.local
COPY data/fail2ban/action.d/* /etc/fail2ban/action.d/
COPY scripts/telegram_alert.py /etc/scripts/telegram_alert.py
COPY scripts/.env /etc/scripts/.env

COPY data/naxsi/naxsi.rules /etc/nginx/naxsi.rules

# Nota: PEP 668
RUN python3 -m venv /venv && \  
    /venv/bin/pip install -r requirements.txt
ENV PATH="/venv/bin:$PATH"

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80 443 5000

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]