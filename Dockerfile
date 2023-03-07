FROM python:3.8-slim

ENV HOME=/root
WORKDIR /root

RUN apt-get update \
    && apt-get install -y python3 python3-pip

RUN python3 -m pip install pyarrow \
    && python3 -m pip install pandas \
    && python3 -m pip install kubernetes

ADD fybrikapplication.py /root
ADD cronjob.py /root

CMD ["python3", "cronjob.py"]

