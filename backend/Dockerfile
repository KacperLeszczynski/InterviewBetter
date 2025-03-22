FROM continuumio/miniconda3

WORKDIR /app

COPY environment.yml .

RUN conda env create -f environment.yml

SHELL ["conda", "run", "-n", "interview_better", "/bin/bash", "-c"]

COPY . .

CMD ["conda", "run", "-n", "interview_better", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
