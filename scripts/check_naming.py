"""Validate QJAI project identifiers and derive registry names."""
import argparse
import os
import re

TYPES = ("agent", "service", "gateway", "bridge", "monitor", "web", "lib", "infra", "lab")
NAME = re.compile(r"qjai-(" + "|".join(TYPES) + r")-[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)
OWNER = re.compile(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", re.ASCII)
RUN_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*", re.ASCII)


def validate_project(name, expected_type=None):
    match = NAME.fullmatch(name)
    if not match or (expected_type and match.group(1) != expected_type):
        raise ValueError("Invalid QJAI project name: expected qjai-<type>-<name> in lowercase kebab-case")
    return name


def registry_image(repository, expected_type=None):
    parts = repository.split("/")
    if len(parts) != 2 or not OWNER.fullmatch(parts[0]):
        raise ValueError("Expected owner/repository")
    owner, name = parts
    validate_project(name, expected_type)
    return f"ghcr.io/{owner.lower()}/{name}"


def test_container_name(project, run_id):
    validate_project(project)
    if not RUN_ID.fullmatch(run_id):
        raise ValueError("Test instance identifier must be lowercase kebab-case")
    return f"{project}-test-{run_id}"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repository", default=os.environ.get("GITHUB_REPOSITORY", ""))
    parser.add_argument("--type", choices=TYPES, default="agent")
    parser.add_argument("--github-env", action="store_true")
    args = parser.parse_args()
    try:
        image = registry_image(args.repository, args.type)
    except ValueError as exc:
        parser.error(str(exc))
    name = args.repository.split("/")[1]
    print(f"Validated {name}: {image}")
    if args.github_env:
        with open(os.environ["GITHUB_ENV"], "a", encoding="utf-8") as out:
            out.write(f"PROJECT_NAME={name}\nIMAGE={image}\n")


if __name__ == "__main__":
    main()
