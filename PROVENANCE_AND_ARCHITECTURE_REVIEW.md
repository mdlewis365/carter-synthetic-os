<!-- SPDX-License-Identifier: AGPL-3.0-only -->

<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Carter Synthetic OS Provenance and Architecture Statement

## Purpose

This document describes the provenance, architectural relationship, and release status of the public **Carter Synthetic OS** repository.

Its purpose is to explain:

* which parts of the public repository descend directly from the private Carter/Synthetic OS codebase;
* which parts were refactored or reimplemented for public release;
* which components were created specifically for the public research runtime;
* how the public runtime differs from the private operational implementation;
* and how AI-assisted engineering tools contributed to the release process.

This document is a technical provenance statement. It is not legal advice, a patent opinion, or a guarantee of behavioral equivalence between the public and private systems.

---

## Current Implementation Reconciliation

This statement was reconciled on 2026-07-27 against private implementation
commit `df0230b9386437a12d8ac4b2c65bf37d68eee9a2`. The public repository baseline
for that comparison is `79a1417809ab96c67968a53b44256863d8fdb7c5`.

The current private code names PGM the **Prompt Governance Module**. Its
executable responsibilities are AMS/RAG retrieval and assembly of those
sources with CRM conversation, the current request, timestamp, configured
Carter name, an application-supplied user label, and prompt-level policy. Many
other named modules inside PGM express model-facing governance responsibilities
through prompt construction. Those responsibilities influence probabilistic
generation and are distinct from deterministic Python enforcement.

The new private commit revises model-facing governance, including its Prime
Directives section, and adds Emergency Claims and Tool-Action Governance.
Public documentation records only the architectural effect: asserted emergency
claims are not thereby verified, and consequential tool actions require
authorization and applicable host controls. The private operative prompt text
is excluded, and prompt instructions are not represented as deterministic
enforcement.

SOSP (Security Operations and Support Protocol) was removed from current PGM;
no SOSP reference remains in tracked private source at commit `df0230b`. The
private host may supply the account email associated with its authenticated
session as PGM contextual identity metadata, but Carter does not independently
verify real-world identity and the email alone does not establish identity or
authority. Session binding and account-context isolation require further
hardening and testing. The privacy boundary is
documented in
[docs/PGM.md](docs/PGM.md), [PRIVACY.md](PRIVACY.md), and
[docs/THREAT_MODEL.md](docs/THREAT_MODEL.md).

This reconciliation updates current architectural claims. It does not rewrite
the source-lineage findings for the public release files or convert current
private prompt text into public implementation provenance.

---

## Originating Architecture

Carter and Synthetic OS were originated and developed by:

**Michael D. Lewis**
Founder, Synthetic OS Labs
Creator and originating architect of Carter and Synthetic OS

Development began in 2023 and continued through the preparation of this initial public research release in 2026.

The originating architecture includes the broader concepts, system organization, subsystem identities, governance philosophy, memory architecture, deterministic-computation boundaries, engineering workflows, ideation workflows, sensory research, and human-review requirements associated with:

* Carter;
* Synthetic Operating System;
* Engineering Assistance System;
* Synthetic Ideation System;
* Carter Sensory Console;
* Math Computation Module;
* Active Memory Subsystem;
* the private Conversation Recovery Module and public rolling-context memory;
* lifecycle and operational reporting;
* prompt and output governance;
* and related deterministic and probabilistic system boundaries.

The public repository exists to make a substantial, inspectable, and runnable portion of that work available for research, evaluation, demonstration, contribution, and technical review.

---

## Overall Provenance Classification

The public repository is best classified as a **mixed-lineage public reference implementation**.

It is not solely:

* a sanitized copy of the private application;
* a direct structural refactor;
* a complete behavioral reimplementation;
* or an entirely new system inspired by private work.

It contains all four relationships.

The repository combines:

1. directly derived and sanitized first-party engineering components;
2. substantially refactored private components;
3. public implementations that reproduce selected private behaviors through new code;
4. and components created specifically to support a safe, reproducible, package-oriented public release.

The result remains recognizably part of the Carter/Synthetic OS system family while intentionally differing from the private operational application.

---

## Directly Derived Components

Several public components retain strong source-level continuity with first-party private code.

These include portions of:

* the Math Computation Module;
* Engineering Decision Record generation;
* EAS engineering governance;
* engineering-domain packs;
* and selected cleared Synthetic Ideation System contracts or schema components.

These materials were relocated, packaged, licensed, sanitized, or lightly adapted for the public repository.

No private engineering records, customer information, conversations, credentials, deployment data, proprietary third-party content, or private runtime databases are intentionally included.

Direct lineage is disclosed to preserve technical honesty and to distinguish original engineering kernels from newly composed public runtime behavior.

---

## Refactored and Reimplemented Components

Other public components preserve the purpose, contracts, or observable behavior of private Carter/Synthetic OS components while using materially different implementations.

These areas include portions of:

* Carter runtime orchestration;
* request and context assembly;
* provider selection and model boundaries;
* session-scoped memory;
* lifecycle monitoring;
* EAS workflow orchestration;
* SIS candidate and evaluator workflows;
* CSC sensory state, transcription, interpretation, and speech boundaries;
* Flask routes and application organization;
* browser interfaces;
* configuration;
* jobs;
* and session management.

These components were refactored or reimplemented to support:

* package-oriented installation;
* reduced coupling;
* public inspection;
* deterministic testing;
* secret-free mock execution;
* bounded inputs and outputs;
* session isolation;
* privacy-safe defaults;
* and clearer separation between probabilistic and deterministic responsibilities.

Behavioral similarity in these areas does not mean that the public runtime is identical to the private application.

---

## Components Created for the Public Release

Some modules and contracts were created or materially designed during preparation of the public repository.

Public-release components include, among others:

* the deterministic mock-provider experience;
* provider-neutral model contracts;
* package-level configuration and validation;
* public workflow schemas;
* a bounded public DIM ingestion interface;
* the experimental public SAL v0 structural-output boundary;
* a metadata-oriented public operation-report format;
* opt-in public persistence interfaces;
* reusable redaction utilities;
* public evidence generation;
* release-focused tests;
* setup and demonstration scripts;
* continuous-integration configuration;
* legal and community documentation;
* and the consolidated public browser interface.

These components support the public reference runtime but should not automatically be interpreted as exact reproductions of private Carter behavior.

Where a public-only component carries an established Synthetic OS subsystem name, its public scope is defined by the code and documentation included in this repository.

---

## Relationship to the Private Carter System

The private Carter/Synthetic OS codebase remains the canonical operational and continuing research implementation maintained by Synthetic OS Labs.

The public repository is:

* an initial public research release;
* a runnable reference implementation;
* a reproducible demonstration environment;
* a technical portfolio and research artifact;
* and a foundation for external inspection and contribution.

It is not represented as:

* a complete copy of private Carter;
* a production deployment;
* a migration of private memory or operational data;
* a reproduction of private accounts or authentication;
* a behavioral clone of the private agent;
* or a substitute for the continuing private research system.

The private implementation includes operational behavior, deployment configuration, identity and continuity material, persistent memory, provider-specific integrations, application workflows, and private data that are intentionally excluded from the public release.

---

## Important Runtime Differences

The public runtime intentionally differs from the private implementation in several ways.

### Identity and continuity

The public runtime uses a bounded public identity policy. It does not include private Carter memories, private conversation history, personal continuity records, or the complete private prompt corpus.

### Memory

Public memory is session-scoped or explicitly opt-in. It does not reproduce the full persistent semantic-memory behavior of private Carter.

### Authentication and sessions

The public application uses a simplified local research-session model. It does not reproduce private production accounts, credentials, role tokens, or deployment authorization behavior.

### Model providers

The default experience uses an explicitly labeled deterministic mock provider.

Optional local and cloud providers may be configured separately. Mock mode demonstrates runtime flow and boundaries; it is not represented as language-model reasoning.

### Jobs and streaming

The public release uses bounded research-oriented job and streaming behavior. It does not guarantee parity with private asynchronous processing, recovery, persistence, or result-streaming behavior.

### EAS

The public Engineering Assistance System retains the directly derived deterministic engineering kernel and governance components while presenting a simplified public workflow.

Public results require qualified human review and do not replace professional engineering judgment, safety review, physical testing, code-compliance review, or licensed approval.

### SIS

The public Synthetic Ideation System is an experimental candidate-generation and evaluation workflow.

Its output does not establish novelty, feasibility, safety, patentability, or scientific correctness.

### CSC

The public Carter Sensory Console is an experimental, session-scoped sensory research interface.

Its interpretation boundary cannot independently authorize:

* responses;
* memory writes;
* tool execution;
* or external actions.

Camera support is limited to explicit browser-preview state unless otherwise documented. Private recordings, voice assets, credentials, and sensory data are not included.

---

## Semantic Adjudication Layer Status

The public `sos.sal` component is an **experimental SAL v0 structural-output boundary**.

Its current purpose is narrow. It can:

* accept bounded structured provider output;
* normalize supported JSON-like values;
* reject malformed or unsupported structures;
* enforce an object-root requirement;
* and return a controlled success or failure result.

It does not currently perform complete semantic adjudication.

It does not establish:

* factual truth;
* intent alignment;
* domain correctness;
* assumption validity;
* memory authority;
* confidence calibration;
* recommendation safety;
* or permission to act.

The broader Semantic Adjudication Layer remains an active architectural and research direction for Carter/Synthetic OS.

Documentation and diagrams should interpret SAL v0 according to the behavior implemented in the current release rather than the full future architectural vision.

---

## Security and Privacy Provenance

The public repository was prepared using a release process intended to exclude private and operationally sensitive material.

The public release is designed not to include:

* passwords;
* access tokens;
* API keys;
* private provider credentials;
* private memories;
* private conversations;
* private job records;
* private logs;
* private databases;
* private recordings;
* production domain or tunnel configuration;
* private voice identifiers or assets;
* or absolute private deployment paths.

Configuration values are supplied through environment variables or safe public defaults.

The repository includes a placeholder-oriented environment example rather than real credentials.

The public application defaults to conservative behavior, including:

* local binding;
* disabled debug mode;
* disabled provider access until configured;
* disabled persistent memory unless enabled;
* disabled sensory retention;
* bounded payloads;
* redacted operational metadata;
* and explicit user activation for microphone or camera features.

These measures reduce exposure but do not constitute a complete production-security certification.

Any network deployment requires an independent review of authentication, authorization, TLS, hosting, secrets, monitoring, retention, provider terms, dependency risk, and AGPL obligations.

---

## AI-Assisted Engineering Disclosure

The public release was prepared through an AI-assisted software-engineering process under the direction and architectural authority of Michael D. Lewis.

AI coding and language-model tools assisted with activities such as:

* repository analysis;
* code comparison;
* refactoring;
* package restructuring;
* implementation of bounded public interfaces;
* test creation;
* documentation;
* release sanitation;
* security review;
* evidence generation;
* and provenance analysis.

AI assistance does not alter the origin of Carter and Synthetic OS or transfer architectural authority away from their creator.

Michael D. Lewis defined the system direction, supplied the originating private architecture and code, established the release objectives and constraints, and retains responsibility for reviewing and approving material public architecture and release claims.

Because AI-generated or AI-modified code can contain mistakes, all public components remain subject to human review, testing, correction, and continuing maintenance.

---

## Architectural Disposition

The repository records the intended public/private relationship below. This
2026-07-27 reconciliation does not itself establish or replace Michael D.
Lewis's human architectural approval. The uncommitted documentation changes and
the current private implementation differences remain subject to his review.

Subject to that review, the proposed description is:

> **Carter Synthetic OS: an initial public research release and reference implementation containing directly derived engineering kernels, refactored and reimplemented Carter/Synthetic OS behavior, and new public-release infrastructure.**

This proposed disposition does not assert that:

* every public component is behaviorally identical to the private system;
* every experimental component is part of the final canonical architecture;
* the software is production-ready;
* the system is professionally certified;
* the system guarantees factual correctness;
* or the system is conscious, sentient, independently sovereign, or AGI.

Future releases may revise public interfaces, subsystem boundaries, naming, workflows, or architectural status as research and implementation continue.

---

## Authorship, Ownership, and Licensing

Unless separately identified, first-party source code and documentation in this repository are provided by:

**Michael D. Lewis, doing business as Synthetic OS Labs**

Copyright:

**Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs**

First-party software is licensed under:

**GNU Affero General Public License version 3 only (`AGPL-3.0-only`)**

Third-party software, generated artifacts, dependencies, exceptions, and notices are documented in the repository’s license and third-party notice files.

Code provenance analysis is not a legal determination of authorship, ownership, patent rights, or license compatibility. Independent legal review may be appropriate before commercial deployment, relicensing, investment, acquisition, or contribution of third-party material.

---

## Verification and Reproducibility

The public repository includes tests, examples, and evidence-generation tools intended to demonstrate the behavior of the public runtime without requiring private data or paid model access.

Where available, release verification should include:

* installation in a clean environment;
* execution of the standard offline test suite;
* generation and checking of reproducible evidence;
* secret scanning of the working tree and Git history;
* dependency review;
* confirmation that documentation matches implemented behavior;
* and review of all release artifacts before publication.

Reproducible evidence generated by mock mode demonstrates public workflow execution and deterministic boundaries. It does not establish equivalence with private Carter or certify the quality of optional model-provider output.

---

## Limitations

This provenance statement has the following limitations:

* It describes the architecture and repository state of the initial public research release.
* It does not compare the public runtime against a certified live production deployment.
* It does not establish legal ownership beyond the stated first-party attribution.
* It does not constitute patent, licensing, security, or regulatory advice.
* It does not guarantee that all defects, secrets, vulnerabilities, or behavioral differences have been discovered.
* It does not claim that refactored or reimplemented behavior is identical to the private source.
* It does not convert experimental public interfaces into permanent architectural commitments.
* It should be reviewed and updated when materially significant repository changes occur.

---

## Release Statement

The Carter Synthetic OS public repository is intentionally transparent about what has been preserved, adapted, reimplemented, newly created, simplified, and excluded.

Its objective is not to create the appearance of complete parity with private Carter.

Its objective is to provide an inspectable and reproducible public expression of the central Carter/Synthetic OS design principle:

> **Probabilistic models may propose, interpret, and reason, but authority, computation, validation, memory, governance, traceability, and permission to act must remain subject to explicit software boundaries and qualified human review.**

That principle connects the directly derived engineering components, the reimplemented public runtime, and the experimental systems introduced for continuing research.

---

**Document status:** Initial Public Research Release
**Current reconciliation:** 2026-07-27 against private commit `df0230b`
**Architectural authority:** Michael D. Lewis
**Organization:** Synthetic OS Labs
**Release year:** 2026
