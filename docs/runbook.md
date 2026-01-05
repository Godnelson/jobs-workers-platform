# Runbook

## Common issues
### API starts but jobs don't run
- check `docker compose logs worker`
- verify Redis healthy
- verify `DATABASE_URL` and `REDIS_URL` in `.env`

### Migrations fail
- `docker compose logs api`
- ensure Postgres is healthy
- rerun: `docker compose down -v && docker compose up --build`

## Scaling
- Start multiple workers:
```bash
docker compose up --scale worker=3
```
- Ensure lock TTL is tuned if tasks run long.
