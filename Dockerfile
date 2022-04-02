# https://pythonspeed.com/articles/conda-docker-image-size/
# The build-stage image:
FROM continuumio/miniconda3 AS build

# Install the package as normal:
WORKDIR /app
COPY environment.yml ./
RUN conda env create -f environment.yml

# Install conda-pack:
RUN conda install -c conda-forge conda-pack

# Use conda-pack to create a standalone enviornment
# in /venv:
RUN conda-pack -n pyart_env -o /tmp/env.tar && \
  mkdir /venv && cd /venv && tar xf /tmp/env.tar && \
  rm /tmp/env.tar

# We've put venv in same path it'll be in final image,
# so now fix up paths:
RUN /venv/bin/conda-unpack


# The runtime-stage image; we can use Debian as the
# base image since the Conda env also includes Python
# for us.
#FROM alpine AS runtime
FROM debian:buster AS runtime

WORKDIR /app
# Copy /venv from the previous stage:
COPY --from=build /venv /venv
COPY server.py ./
COPY ingestor.py ./
COPY merra.py ./
COPY message_queue.py ./
COPY radar.yml ./
COPY plot.yml ./
COPY nasa_plot.yml ./

# When image is run, run the code with the environment
# activated:
SHELL ["/bin/bash", "-c"]
ENTRYPOINT source /venv/bin/activate && FLASK_APP=server.py FLASK_ENV=production flask run -h 0.0.0.0 -p 5000
# https://stackoverflow.com/a/71669914/5379453
#ENTRYPOINT source /venv/bin/activate && python server.py
#RUN chmod +x ./entrypoint.sh
#ENTRYPOINT ["/bin/sh", "-c", "source /venv/bin/activate && python server.py"]
