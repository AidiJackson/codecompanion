# FastAPI Endpoints Documentation

## Health Check Endpoint

### GET /health

Returns system health status with event bus and database connectivity information.

**Response Format:**
```json
{
  "ok": true,
  "event_bus": "mock|redis",
  "redis_ok": boolean,
  "db_ok": boolean
}
```

**Response Fields:**
- `ok`: Always `true` if the endpoint is accessible
- `event_bus`: Current event bus configuration ("mock" or "redis")
- `redis_ok`: `true` if Redis is configured and accessible, `false` otherwise
- `db_ok`: `true` if database connection is working

**Example Response:**
```json
{
  "ok": true,
  "event_bus": "mock",
  "redis_ok": false,
  "db_ok": true
}
```

**Curl Example:**
```bash
curl -X GET http://localhost:8000/health
```

---

## Task Simulation Endpoint (Development Only)

### POST /simulate_task

Creates a simulated task for development and testing purposes. Publishes a TASK_CREATED event to the event bus and broadcasts to WebSocket clients.

**Request Body:**
```json
{
  "objective": "string"
}
```

**Request Fields:**
- `objective`: Description of the simulated task objective

**Response Format:**
```json
{
  "task_id": "sim_task_xxxxxxxx"
}
```

**Response Fields:**
- `task_id`: Unique identifier for the simulated task

**Example Request:**
```json
{
  "objective": "Create a sample web application with user authentication"
}
```

**Example Response:**
```json
{
  "task_id": "sim_task_a1b2c3d4"
}
```

**Curl Example:**
```bash
curl -X POST http://localhost:8000/simulate_task \
     -H "Content-Type: application/json" \
     -d '{"objective": "Create a sample web application"}'
```

**Event Publishing:**
- Publishes to `EventStreamType.TASKS` stream
- Event type: `EventType.TASK_CREATED`
- Includes task metadata and correlation ID
- Broadcasts to connected WebSocket clients

---

## Implementation Notes

### Health Check Logic
- Checks Redis connectivity only if EVENT_BUS is set to "redis"
- Database check uses SQLite connection test
- Returns structured status information for monitoring

### Task Simulation Features
- Generates unique task IDs with `sim_task_` prefix
- Creates complete StreamEvent with correlation tracking
- Supports WebSocket real-time notifications
- Includes comprehensive error handling

### Error Responses
Both endpoints return appropriate HTTP status codes:
- `200`: Success
- `500`: Internal server error
- `503`: Service unavailable (orchestrator not available)

### Security Considerations
The simulate_task endpoint is intended for development use only. In production environments, consider:
- Adding authentication/authorization
- Rate limiting
- Input validation and sanitization
- Audit logging for task creation events