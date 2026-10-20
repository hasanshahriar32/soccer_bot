.PHONY: paper analysis replay figures check package
paper:
	bash compile.sh
analysis:
	python3 experiments/characterize_hazbot.py
	python3 experiments/verify_hazbot_mission.py
replay:
	python3 experiments/replay_supervisor.py
figures:
	python3 scripts/build_figures.py
check:
	python3 experiments/characterize_hazbot.py --output-dir /tmp/hazbot-characterization-check
	python3 experiments/verify_hazbot_mission.py --output-dir /tmp/hazbot-mission-check
	python3 scripts/check_submission.py
package:
	python3 scripts/package_sources.py
