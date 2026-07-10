"""
Shared mock-repository singletons (USE_MOCK_DB=true).

Both the FastAPI DI layer (app/api/dependencies.py) and the judge worker
(app/services/queue/runtime.py) must hit the SAME in-memory instances, so
they live here rather than inside dependencies.py.
"""

from app.repositories.problem_repository import MockProblemRepository
from app.repositories.submission_repository import MockSubmissionRepository
from app.repositories.testcase_repository import MockTestCaseRepository
from app.repositories.user_repository import MockUserRepository

mock_user_repo = MockUserRepository()
mock_problem_repo = MockProblemRepository()
mock_testcase_repo = MockTestCaseRepository()
mock_submission_repo = MockSubmissionRepository()
