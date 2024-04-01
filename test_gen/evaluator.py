import ast
import os

import coverage
import pytest


class TestEvaluator:
    def __init__(self, tesing_dir: str):
        self._testing_dir = tesing_dir
    
    def build_test(self, test: str) -> bool:
        try:
            ast.parse(test)
        except SyntaxError:
            return False
        return True
    
    def run_test_successfully(self, test: str) -> bool:
        try:
            pytest.main(["-c", test])
        except Exception:
            return False
        return True
        
    def _compute_coverage(self) -> float:
        # Start coverage measurement
        cov = coverage.Coverage(source=[self._testing_dir])
        cov.start()
        # Run pytest
        pytest.main([self._testing_dir])
        # Stop coverage measurement
        cov.stop()
        cov.save()

        # Report and get coverage data
        cov.report()
        data = cov.get_data()

        # Calculate coverage percentage
        covered = data.numbers.n_executed
        total = data.numbers.n_executable
        coverage_percentage = (covered / total) * 100 if total > 0 else 100
        return coverage_percentage

    def difference_in_coverage(self, test: str) -> float:
        original_coverage = self._compute_coverage()
        with open(os.path.join(self._testing_dir, "temp_test.py"), "w") as f:
            f.write(test)
        new_coverage = self._compute_coverage()
        os.remove(os.path.join(self._testing_dir, "temp_test.py"))
        return new_coverage - original_coverage
    
    def run(self, test: str) -> bool:
        if not self.build_test(test):
            return False
        if not self.run_test_successfully(test):
            return False
        if self.difference_in_coverage(test) <= 0:
            return False
        return True
