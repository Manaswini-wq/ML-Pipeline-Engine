# ML Pipeline Platform

A lightweight, self-contained ML platform that automates training, evaluation, model comparison, registry management, and automated retraining. Demonstrates the core infrastructure patterns behind production ML platforms like SageMaker Pipelines, Kubeflow, and MLflow.

---

## Architecture

### Pipeline Execution Engine

```
                     +------------------+
                     |  Pipeline DAG    |
                     |  Definition      |
                     |  (Python DSL)    |
                     +--------+---------+
                              |
                     +--------v---------+
                     |  DAG Scheduler   |
                     |  (Kahn's algo    |
                     |   topological    |
                     |   sort)          |
                     +--------+---------+
                              |
               +--------------+--------------+
               |              |              |
        +------v------+ +----v------+ +-----v------+
        | Ingest Task | | Feature   | | Validate   |
        |             | | Task      | | Task       |
        +------+------+ +----+------+ +-----+------+
               |              |              |
               +--------------+--------------+
                              |
               +--------------+--------------+
               |                             |
        +------v------+              +------v-------+
        | Train Task  |              | Train Task   |
        | (LightGBM)  |              | (Logistic)   |
        +------+------+              +------+-------+
               |                            |
               +-------------+--------------+
                             |
                    +--------v---------+
                    | Evaluate &       |
                    | Compare Models   |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Validate &       |
                    | Register Best    |
                    +--------+---------+
                             |
                    +--------v---------+
                    | Promote to       |
                    | Production       |
                    +------------------+
```

### Automated Retraining Loop

```
  +-------------------+       +-------------------+       +-------------------+
  |  Performance      | ----> | Retrain Trigger   | ----> | Pipeline          |
  |  Monitor          |       |                   |       | Executor          |
  |                   |       | Checks:           |       |                   |
  | - Track AUC over  |       | - AUC drop > 0.02|       | - Re-runs full    |
  |   time            |       | - Model age > 7d  |       |   DAG pipeline    |
  | - Compare vs      |       | - Manual trigger  |       | - Auto-compares   |
  |   baseline        |       |                   |       |   new vs old      |
  +-------------------+       +-------------------+       +-------------------+
                                                                    |
                                                          +---------v----------+
                                                          | Model Validator    |
                                                          |                    |
                                                          | Quality gates:     |
                                                          | - Min AUC >= 0.65  |
                                                          | - No regression    |
                                                          |   vs production    |
                                                          | - Min 1000 eval    |
                                                          |   samples          |
                                                          | - Auto-promote if  |
                                                          |   all gates pass   |
                                                          +--------------------+
```

### Model Registry Lifecycle

```
  +-------+       +---------+       +------------+       +----------+
  |  Dev  | ----> | Staging | ----> | Production | ----> | Archived |
  +-------+       +---------+       +------------+       +----------+

  - Register: model enters as "dev"
  - Promote to staging: passes basic validation
  - Promote to production: passes all quality gates, old prod auto-archived
  - Archive: replaced by newer production model
```

---

## Key Features

| Feature | Description |
|---------|-------------|
| **DAG Pipeline Engine** | Define ML pipelines as directed acyclic graphs with dependency resolution and parallel task execution |
| **Topological Scheduling** | Kahn's algorithm groups tasks into execution levels; tasks within a level run in parallel |
| **Experiment Tracker** | Log parameters, metrics, and artifacts for every run with cross-experiment comparison |
| **Model Registry** | Version, stage (dev/staging/prod/archived), and promote models with full lineage |
| **Artifact Store** | Content-addressable storage using SHA256 hashing for deduplication and integrity |
| **Automated Retraining** | Trigger retraining on performance degradation, model staleness, or schedule |
| **Validation Gates** | Automatic quality checks (min AUC, no regression, min sample size) before promotion |
| **Pipeline Monitoring** | Track task durations, success rates, and failure counts across all runs |

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Pipeline Engine | Custom DAG executor with topological sort |
| Experiment Tracking | JSON-based tracker |
| Model Registry | File-based with JSON metadata index |
| Artifact Store | Local filesystem with SHA256 content addressing |
| Dashboard API | FastAPI |
| ML Models | LightGBM, Scikit-learn |
| Containerization | Docker |
| CI/CD | GitHub Actions |
| Testing | pytest |

---

## Project Structure

```
ml-pipeline-platform/
|
+-- README.md
+-- requirements.txt
+-- setup.py
+-- Dockerfile
+-- docker-compose.yml
+-- .gitignore
|
+-- .github/workflows/
|   +-- ci.yml
|
+-- configs/
|   +-- default.yaml
|
+-- scripts/
|   +-- run_pipeline.py           # Execute full ML training pipeline
|   +-- run_dashboard.py          # Start platform dashboard API
|   +-- register_model.py         # Manually register a model
|
+-- src/
|   +-- utils/
|   |   +-- logger.py             # Structured JSON logging
|   |   +-- config.py             # Pydantic-based configuration
|   |
|   +-- pipeline/
|   |   +-- task.py               # Task definition with retry logic
|   |   +-- dag.py                # DAG with topological sort + validation
|   |   +-- executor.py           # Parallel executor with checkpointing
|   |   +-- scheduler.py          # Interval-based pipeline scheduling
|   |
|   +-- experiment/
|   |   +-- tracker.py            # Log experiments as JSON files
|   |   +-- comparator.py         # Cross-experiment comparison tables
|   |
|   +-- registry/
|   |   +-- model_registry.py     # Model versioning + stage promotion
|   |   +-- artifact_store.py     # SHA256 content-addressable storage
|   |
|   +-- retraining/
|   |   +-- trigger.py            # Performance + staleness triggers
|   |   +-- validator.py          # Quality gate validation
|   |
|   +-- serving/
|   |   +-- api.py                # FastAPI dashboard endpoints
|   |
|   +-- monitoring/
|       +-- pipeline_monitor.py   # Pipeline run stats + task performance
|
+-- tests/
    +-- test_dag.py
    +-- test_executor.py
    +-- test_registry.py
    +-- test_trigger.py
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run a full ML pipeline

```bash
python scripts/run_pipeline.py
```

This single command:
- Generates synthetic classification data (10K samples, 20 features)
- Trains LightGBM and Logistic Regression in parallel
- Evaluates both on test set, picks the best by AUC
- Validates against quality gates (min AUC, min eval samples)
- Registers and promotes the best model to production
- Saves pipeline run details to pipeline_runs/

Output:
```
Pipeline DAG:
  ['generate_data']
  ['train_lightgbm', 'train_logistic']
  ['evaluate']
  ['register']

Pipeline run_ml_training_pipeline_1695000000: completed
  generate_data: completed (0.12s)
  train_lightgbm: completed (1.45s)
  train_logistic: completed (0.34s)
  evaluate: completed (0.08s)
  register: completed (0.05s)

Best model registered: v1695000000
  Metrics: {'auc': 0.9234, 'logloss': 0.2891}
```

### 3. Start the platform dashboard

```bash
python scripts/run_dashboard.py --port 8000
```

### 4. Explore via API

```bash
# List all pipeline runs
curl http://localhost:8000/pipelines

# List experiments
curl http://localhost:8000/experiments

# List registered models
curl http://localhost:8000/models

# Promote a model
curl -X POST "http://localhost:8000/models/classifier/promote?version=v1&stage=production"
```

---

## Docker

```bash
docker-compose up --build
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/pipelines` | List all pipeline runs with status and duration |
| `GET` | `/pipelines/{run_id}` | Get detailed run info with per-task results |
| `GET` | `/experiments` | List all tracked experiments |
| `GET` | `/experiments/{exp_id}` | Get experiment params, metrics, artifacts |
| `GET` | `/models` | List all registered models and versions |
| `GET` | `/models/{name}/versions` | List versions for a specific model |
| `POST` | `/models/{name}/promote` | Promote a model version to a stage |
| `GET` | `/health` | Health check |

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Custom DAG engine (not Airflow) | Lightweight, zero external dependencies, demonstrates core concepts |
| Kahn's algorithm for scheduling | Correct topological ordering with natural level-based parallelism |
| Thread pool execution | Tasks in same level run in parallel; simple and effective for I/O + CPU mix |
| JSON-based experiment tracking | Human-readable, git-friendly, no database dependency |
| Content-addressable artifact store | SHA256 deduplication prevents storing identical models twice |
| Stage-based model lifecycle | Clear promotion path (dev -> staging -> prod -> archived) with auto-archival |
| Quality gates before promotion | Prevents deploying models that regress or fail minimum performance bars |
| Staleness-based retraining | Models degrade over time due to data drift; age limit forces periodic refresh |

---

## License

MIT
