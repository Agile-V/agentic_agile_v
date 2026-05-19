.PHONY: test validate-evidence new-feature new-bug

test:
	@echo "Add project-specific tests here."

validate-evidence:
	python scripts/validate_evidence.py --root evidence

new-feature:
	python scripts/new_task.py --type feature --id AAV-001 --title "Example feature"

new-bug:
	python scripts/new_task.py --type bug --id AAV-002 --title "Example bug"
