# Thai Segmentation System Server

## Development

### Backend

To run the backend server, navigate to the `backend` directory and execute:

```bash
uv run main.py
```

#### Benchmarking Endpoint Speed

First, start the backend server as described above. Then, benchmark the speed of the NLP endpoints with the following command:

```bash
uv run python scripts/nlp_utils/benchmark_endpoint_speed.py --base-url "http://127.0.0.1:8000" --repeats 3 --lengths "250,500,1000,2000,4000,6000,8000,10000"
```

### Frontend

To run the frontend development server, navigate to the `frontend` directory and execute:

```bash
npm install # run once
npm run dev
```
