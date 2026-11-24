from automation.service import WorkflowService

def test_workflow_completes_and_records_events(tmp_path):
    service = WorkflowService(database_path=str(tmp_path / "workflow.db"))
    result = service.run("C-1001", "Send the quarterly schedule.", "test-key-1")
    assert result["status"] == "completed"
    assert result["attempts"] == 1
    assert [event["step"] for event in result["events"]][-1] == "deliver_notification"

def test_idempotency_returns_existing_run(tmp_path):
    service = WorkflowService(database_path=str(tmp_path / "workflow.db"))
    first = service.run("C-1001", "Send a notice.", "duplicate-key")
    second = service.run("C-1001", "Send a notice again.", "duplicate-key")
    assert first["run_id"] == second["run_id"]

def test_unknown_customer_fails_gracefully(tmp_path):
    service = WorkflowService(database_path=str(tmp_path / "workflow.db"))
    result = service.run("C-9999", "Hello.", "bad-customer")
    assert result["status"] == "failed"
    assert "not found" in result["result"]["error"]

def test_delivery_retries_then_succeeds(tmp_path):
    attempts = {"count": 0}
    def flaky_delivery(payload):
        attempts["count"] += 1
        if attempts["count"] < 2:
            raise RuntimeError("temporary downstream error")
    service = WorkflowService(
        database_path=str(tmp_path / "workflow.db"),
        max_attempts=3,
        retry_delay_seconds=0,
        delivery_adapter=flaky_delivery,
    )
    result = service.run("C-1002", "Confirm receipt.", "retry-key")
    assert result["status"] == "completed"
    assert result["attempts"] == 2
