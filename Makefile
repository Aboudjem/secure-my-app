# The one test command. CI runs exactly this on every push and pull request.
#   make test   runs the three suites and prints each count
.PHONY: test

test:
	python3 evals/check_skill.py skills/secure-my-app/SKILL.md
	python3 tests/test_manifests.py
	python3 tests/test_fixture.py
