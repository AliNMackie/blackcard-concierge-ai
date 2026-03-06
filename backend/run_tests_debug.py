import pytest
import sys

class MyPlugin:
    def pytest_sessionfinish(self, session, exitstatus):
        print(f"\nFinal exit status: {exitstatus}")

if __name__ == "__main__":
    # Run only test_api.py to keep it focused
    pytest.main(["tests/test_api.py", "-v", "-s"], plugins=[MyPlugin()])
