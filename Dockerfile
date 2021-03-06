FROM python:3
ENV PYTHONUNBUFFERED 1
WORKDIR /usr/src/mysite

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY ./mysite .
RUN mkdir docs

RUN mkdir -p /vol/web/media
RUN mkdir -p /vol/web/static

RUN adduser --disabled-password user
RUN chown -R user:user /usr/src
RUN chown -R user:user /vol/
RUN chmod -R 755 /vol/web
USER user
