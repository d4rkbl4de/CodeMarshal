---
name: Docker GA Validation v2.2.0
about: Validate blocked Docker gates for v2.2.0 GA
title: "Release follow-up: Docker GA validation for v2.2.0"
labels: ["release", "docker", "follow-up"]
assignees: []
---

## Context

`v2.2.0` was tagged with Docker validation blocked on the release machine because Docker CLI was unavailable.

Reference checklist: `docs/RELEASE_CHECKLIST_v2.2.0.md`

## Required Validation

- [ ] `docker build -f Dockerfile -t codemarshal:latest .`
- [ ] `docker build -f Dockerfile.dev -t codemarshal:dev .`

## Acceptance Criteria

- [ ] Both Docker builds complete successfully on CI or a Docker-enabled release runner.
- [ ] Any failures include first actionable root cause and remediation.
- [ ] `docs/RELEASE_CHECKLIST_v2.2.0.md` is updated with PASS/FAIL evidence and timestamp.

## Notes

- Keep scope limited to Docker validation for the `v2.2.0` release line.
