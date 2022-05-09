# set base image (host OS)
FROM python:3.9

# update
RUN apt-get update -q -y && apt-get install -q -y dnsutils

# set the working directory in the container
WORKDIR /code

# copy the dependencies file to the working directory
COPY requirements.txt .

# install dependencies
RUN pip install -r requirements.txt

# copy the content of the local src directory to the working directory
COPY . .

# TODO handle DNS params via env variable
RUN DOMAIN='api.binance.com'; IP=$(dig ${DOMAIN} +short); echo $DOMAIN $IP >> /etc/resolv.conf
RUN DOMAIN='api.coingecko.com'; IP=$(dig ${DOMAIN} +short); echo $DOMAIN $IP >> /etc/resolv.conf

# command to run on container start
CMD [ "python", "./price_alert.py" ]