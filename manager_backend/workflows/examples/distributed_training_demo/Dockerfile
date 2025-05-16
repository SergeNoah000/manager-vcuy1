#manager_backend/workflows/examples/distributed_training_demo/split_dataset.py

FROM python:3.10-slim

WORKDIR /app
COPY . /app
RUN pip install torch torchvision

ENTRYPOINT ["python", "train_on_shard.py"]
