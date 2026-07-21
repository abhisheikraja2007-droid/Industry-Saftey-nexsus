FROM python:3.11-slim
WORKDIR /app

RUN pip install --no-cache-dir paho-mqtt==1.6.1 numpy==1.26.4 pandas==2.2.2

# Copy simulator code
COPY simulator/ ./simulator/

# Copy the data package the simulator imports
COPY data/ ./data/

# Create __init__.py files so Python treats directories as packages
RUN touch data/__init__.py data/synthetic/__init__.py

ENV PYTHONPATH=/app

WORKDIR /app/simulator

CMD ["python", "data_simulator.py"]
