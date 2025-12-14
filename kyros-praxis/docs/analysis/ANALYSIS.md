# Repository Analysis
Date: 2025-09-15T04:19:51.989765Z


## Ruff (Python)

````
[Errno 2] No such file or directory: 'ruff'
````



## Pytest

````
2025-09-15 05:19:53 - app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - app.core.logging - INFO - Orchestrator event logging configured for o-glm -> .devlogs/orch-o-glm.log
2025-09-15 05:19:53 - main - INFO - Orchestrator starting with ORCH_ID: o-glm

==================================== ERRORS ====================================
__ ERROR collecting packages/service-registry/tests/contract/test_registry.py __
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/packages/service-registry/tests/contract/test_registry.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
packages/service-registry/tests/contract/test_registry.py:4: in <module>
    from packages.service_registry.main import app
E   ModuleNotFoundError: No module named 'packages'
___ ERROR collecting packages/service-registry/tests/unit/test_discovery.py ____
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/packages/service-registry/tests/unit/test_discovery.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
packages/service-registry/tests/unit/test_discovery.py:3: in <module>
    from packages.service_registry.main import get_service, register_service
E   ModuleNotFoundError: No module named 'packages'
______ ERROR collecting services/orchestrator/tests/contract/test_jobs.py ______
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/tests/contract/test_jobs.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
services/orchestrator/main.py:368: in <module>
    from .routers import openai
services/orchestrator/routers/openai.py:11: in <module>
    from app.core.openai_agent import sync_agent, async_agent
E   ModuleNotFoundError: No module named 'app'

During handling of the above exception, another exception occurred:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services/orchestrator/tests/contract/test_jobs.py:6: in <module>
    from services.orchestrator.main import app
services/orchestrator/main.py:370: in <module>
    import routers.openai as openai  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'routers'
------------------------------- Captured stdout --------------------------------
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Orchestrator event logging configured for o-glm -> .devlogs/orch-o-glm.log
2025-09-15 05:19:53 - services.orchestrator.main - INFO - Orchestrator starting with ORCH_ID: o-glm
2025-09-15 05:19:53 - services.orchestrator.main - WARNING - SlowAPI not available, rate limiting disabled
2025-09-15 05:19:53 - services.orchestrator.security_middleware - INFO - Security middleware configured
__________ ERROR collecting services/orchestrator/tests/test_auth.py ___________
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/tests/test_auth.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
services/orchestrator/main.py:368: in <module>
    from .routers import openai
services/orchestrator/routers/openai.py:11: in <module>
    from app.core.openai_agent import sync_agent, async_agent
E   ModuleNotFoundError: No module named 'app'

During handling of the above exception, another exception occurred:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services/orchestrator/tests/test_auth.py:6: in <module>
    from services.orchestrator.main import app
services/orchestrator/main.py:370: in <module>
    import routers.openai as openai  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'routers'
------------------------------- Captured stdout --------------------------------
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Orchestrator event logging configured for o-glm -> .devlogs/orch-o-glm.log
2025-09-15 05:19:53 - services.orchestrator.main - INFO - Orchestrator starting with ORCH_ID: o-glm
2025-09-15 05:19:53 - services.orchestrator.main - WARNING - SlowAPI not available, rate limiting disabled
2025-09-15 05:19:53 - services.orchestrator.security_middleware - INFO - Security middleware configured
__ ERROR collecting services/orchestrator/tests/test_backend_steel_thread.py ___
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/tests/test_backend_steel_thread.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
services/orchestrator/main.py:368: in <module>
    from .routers import openai
services/orchestrator/routers/openai.py:11: in <module>
    from app.core.openai_agent import sync_agent, async_agent
E   ModuleNotFoundError: No module named 'app'

During handling of the above exception, another exception occurred:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services/orchestrator/tests/test_backend_steel_thread.py:10: in <module>
    from services.orchestrator.main import app
services/orchestrator/main.py:370: in <module>
    import routers.openai as openai  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'routers'
------------------------------- Captured stdout --------------------------------
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Orchestrator event logging configured for o-glm -> .devlogs/orch-o-glm.log
2025-09-15 05:19:53 - services.orchestrator.main - INFO - Orchestrator starting with ORCH_ID: o-glm
2025-09-15 05:19:53 - services.orchestrator.main - WARNING - SlowAPI not available, rate limiting disabled
2025-09-15 05:19:53 - services.orchestrator.security_middleware - INFO - Security middleware configured
__________ ERROR collecting services/orchestrator/tests/test_main.py ___________
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/tests/test_main.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
services/orchestrator/main.py:368: in <module>
    from .routers import openai
services/orchestrator/routers/openai.py:11: in <module>
    from app.core.openai_agent import sync_agent, async_agent
E   ModuleNotFoundError: No module named 'app'

During handling of the above exception, another exception occurred:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services/orchestrator/tests/test_main.py:3: in <module>
    from services.orchestrator.main import app
services/orchestrator/main.py:370: in <module>
    import routers.openai as openai  # type: ignore
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   ModuleNotFoundError: No module named 'routers'
------------------------------- Captured stdout --------------------------------
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Logging configured
2025-09-15 05:19:53 - services.orchestrator.app.core.logging - INFO - Orchestrator event logging configured for o-glm -> .devlogs/orch-o-glm.log
2025-09-15 05:19:53 - services.orchestrator.main - INFO - Orchestrator starting with ORCH_ID: o-glm
2025-09-15 05:19:53 - services.orchestrator.main - WARNING - SlowAPI not available, rate limiting disabled
2025-09-15 05:19:53 - services.orchestrator.security_middleware - INFO - Security middleware configured
______ ERROR collecting services/orchestrator/tests/test_openai_agent.py _______
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/tests/test_openai_agent.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
services/orchestrator/tests/test_openai_agent.py:8: in <module>
    from app.core.openai_agent import OpenAIAgent
E   ModuleNotFoundError: No module named 'app'
__________________ ERROR collecting test_escalation_system.py __________________
ImportError while importing test module '/home/thomas/kyros-praxis/kyros-praxis/test_escalation_system.py'.
Hint: make sure your test modules/packages have valid Python names.
Traceback:
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
test_escalation_system.py:33: in <module>
    from escalation_workflow import (
services/orchestrator/escalation_workflow.py:149: in <module>
    from .escalation_triggers import (
E   ImportError: attempted relative import with no known parent package
____________________ ERROR collecting zen-mcp-server/tests _____________________
/usr/lib/python3.13/importlib/__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
/usr/lib/python3.13/site-packages/_pytest/assertion/rewrite.py:186: in exec_module
    exec(co, module.__dict__)
zen-mcp-server/tests/conftest.py:36: in <module>
    from providers import ModelProviderRegistry  # noqa: E402
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
zen-mcp-server/providers/__init__.py:4: in <module>
    from .gemini import GeminiModelProvider
zen-mcp-server/providers/gemini.py:11: in <module>
    from google import genai
E   ImportError: cannot import name 'genai' from 'google' (unknown location)
=============================== warnings summary ===============================
services/orchestrator/models.py:123
services/orchestrator/models.py:123
  /home/thomas/kyros-praxis/kyros-praxis/services/orchestrator/models.py:123: MovedIn20Warning: The ``declarative_base()`` function is now available as sqlalchemy.orm.declarative_base(). (deprecated since: 2.0) (Background on SQLAlchemy 2.0 at: https://sqlalche.me/e/b8d9)
    Base = declarative_base()

tests/test_escalation_scenarios.py:40
  /home/thomas/kyros-praxis/kyros-praxis/tests/test_escalation_scenarios.py:40: PytestCollectionWarning: cannot collect test class 'TestScenario' because it has a __init__ constructor (from: tests/test_escalation_scenarios.py)
    @dataclass

zen-mcp-server/simulator_tests/test_consensus_conversation.py:14
  /home/thomas/kyros-praxis/kyros-praxis/zen-mcp-server/simulator_tests/test_consensus_conversation.py:14: PytestCollectionWarning: cannot collect test class 'TestConsensusConversation' because it has a __init__ constructor (from: zen-mcp-server/simulator_tests/test_consensus_conversation.py)
    class TestConsensusConversation(ConversationBaseTest):

zen-mcp-server/simulator_tests/test_consensus_three_models.py:10
  /home/thomas/kyros-praxis/kyros-praxis/zen-mcp-server/simulator_tests/test_consensus_three_models.py:10: PytestCollectionWarning: cannot collect test class 'TestConsensusThreeModels' because it has a __init__ constructor (from: zen-mcp-server/simulator_tests/test_consensus_three_models.py)
    class TestConsensusThreeModels(BaseSimulatorTest):

zen-mcp-server/simulator_tests/test_consensus_workflow_accurate.py:18
  /home/thomas/kyros-praxis/kyros-praxis/zen-mcp-server/simulator_tests/test_consensus_workflow_accurate.py:18: PytestCollectionWarning: cannot collect test class 'TestConsensusWorkflowAccurate' because it has a __init__ constructor (from: zen-mcp-server/simulator_tests/test_consensus_workflow_accurate.py)
    class TestConsensusWorkflowAccurate(ConversationBaseTest):

zen-mcp-server/simulator_tests/test_model_thinking_config.py:12
  /home/thomas/kyros-praxis/kyros-praxis/zen-mcp-server/simulator_tests/test_model_thinking_config.py:12: PytestCollectionWarning: cannot collect test class 'TestModelThinkingConfig' because it has a __init__ constructor (from: zen-mcp-server/simulator_tests/test_model_thinking_config.py)
    class TestModelThinkingConfig(BaseSimulatorTest):

zen-mcp-server/simulator_tests/test_testgen_validation.py:16
  /home/thomas/kyros-praxis/kyros-praxis/zen-mcp-server/simulator_tests/test_testgen_validation.py:16: PytestCollectionWarning: cannot collect test class 'TestGenValidationTest' because it has a __init__ constructor (from: zen-mcp-server/simulator_tests/test_testgen_validation.py)
    class TestGenValidationTest(ConversationBaseTest):

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
ERROR packages/service-registry/tests/contract/test_registry.py
ERROR packages/service-registry/tests/unit/test_discovery.py
ERROR services/orchestrator/tests/contract/test_jobs.py
ERROR services/orchestrator/tests/test_auth.py
ERROR services/orchestrator/tests/test_backend_steel_thread.py
ERROR services/orchestrator/tests/test_main.py
ERROR services/orchestrator/tests/test_openai_agent.py
ERROR test_escalation_system.py
ERROR zen-mcp-server/tests - ImportError: cannot import name 'genai' from 'go...
!!!!!!!!!!!!!!!!!!! Interrupted: 9 errors during collection !!!!!!!!!!!!!!!!!!!!
8 warnings, 9 errors in 1.31s
````



## ESLint (console)

````
> kyros-console@0.1.0 lint
> next lint



./app/(dashboard)/jobs/[id]/page.tsx
263:71  Error: `'` can be escaped with `&apos;`, `&lsquo;`, `&#39;`, `&rsquo;`.  react/no-unescaped-entities

info  - Need to disable some ESLint rules? Learn more here: https://nextjs.org/docs/basic-features/eslint#disabling-rules
````



## Jest (console)

````
PASS app/(dashboard)/agents/__tests__/page.test.tsx
PASS __tests__/agents.test.tsx
PASS __tests__/settings.test.tsx
PASS __tests__/dashboard.test.tsx

Test Suites: 1 skipped, 4 passed, 4 of 5 total
Tests:       2 skipped, 18 passed, 20 total
Snapshots:   0 total
Time:        1.027 s
Ran all test suites.
````

