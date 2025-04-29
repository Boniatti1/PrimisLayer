FROM nginx:alpine

RUN apk add python3 py3-pip supervisor

COPY dashboard/ /dashboard/
COPY ./requirements.txt requirements.txt
COPY data/nginx.conf /etc/nginx/nginx.conf
COPY data/protected_routes.conf /etc/nginx/protected_routes.conf

# Nota: PEP 668
RUN python3 -m venv /venv && \
    /venv/bin/pip install -r requirements.txt
ENV PATH="/venv/bin:$PATH"

COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 80 5000

CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]