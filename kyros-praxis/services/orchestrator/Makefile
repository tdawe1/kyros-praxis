SHELL := /bin/bash

.PHONY: test-events test-thread test-auth

test-events:
	pytest services/orchestrator/tests/unit/test_events.py -q

test-thread:
	pytest -q \
	  services/orchestrator/tests/unit/test_endpoints.py::test_healthz_ok \
	  services/orchestrator/tests/unit/test_endpoints.py::test_create_task_and_list \
	  services/orchestrator/tests/test_auth.py::test_unauth_create \
	  services/orchestrator/tests/test_auth.py::test_login_invalid \
	  services/orchestrator/tests/test_auth.py::test_login_and_create

test-auth:
	pytest -q services/orchestrator/tests/test_auth.py

