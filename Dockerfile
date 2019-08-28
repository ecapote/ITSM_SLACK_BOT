FROM python:3.7.4-alpine
RUN mkdir /app
RUN mkdir /logs
WORKDIR /app
COPY ./py_ITSM_BOT_25.py /app
COPY ./slack_bot_config.ini /app
RUN pip install requests slackclient
CMD ["python","/app/py_ITSM_BOT_25.py"]
