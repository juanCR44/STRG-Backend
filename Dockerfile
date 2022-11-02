FROM homebrew/ubuntu20.04
COPY requirements.txt /app/requirements.txt

RUN sudo apt-get update
RUN sudo apt-get install -y python3-pip
RUN sudo pip3 install pipenv
RUN sudo pip3 install ez_setup
RUN sudo pip3 install gunicorn

RUN sudo pip3 install --upgrade pip setuptools wheel
RUN sudo apt-get install musl-dev linux-headers-generic g++ gcc zlib1g-dev make python3-dev libjpeg-dev libgl1-mesa-glx libglib2.0-0 --assume-yes 
RUN sudo pip3 install importlib_metadata

RUN sudo apt-get update && sudo apt-get install --assume-yes cmake \ 
                        #openblas-dev \ 
                        libopenblas-dev \ 
                        gfortran \ 
                        musl-dev \ 
                        libffi-dev \
                        gcc \
                        libc-dev

RUN set -ex \
    && sudo pip3 install --upgrade pip \
    && sudo pip3 install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host=files.pythonhosted.org --no-cache-dir -r /app/requirements.txt

WORKDIR /app
ADD . .

CMD gunicorn stckrcgntBackend.wsgi:application --bind 0.0.0.0:$PORT
