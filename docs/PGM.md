<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2023-2026 Michael D. Lewis, doing business as Synthetic OS Labs -->

# Prompt Governance Module

This document reconciles the public documentation with the committed private
implementation at commit `df0230b9386437a12d8ac4b2c65bf37d68eee9a2`
(2026-07-27). It describes the private implementation for architectural
comparison. The public `0.1.0` source tree does not contain
`SynCogOS_PGM.py` or reproduce its complete prompt corpus.

## Terminology

The official current expansion of PGM is **Prompt Governance Module**, matching
`SynCogOS_PGM.py`. **Program Guidance Matrix** is an earlier project term. It
may appear in historical material, but it is not the current component name.

## Verified Executable Responsibilities

The current Python implementation:

1. retrieves relevant context from the Active Memory Subsystem (AMS);
2. retrieves relevant knowledge from the Retrieval-Augmented Generation (RAG)
   subsystem;
3. assembles those results with the current CRM conversation, user request,
   timestamp, configured Carter name, an application-supplied user label, and
   a large body of prompt-level governance instructions;
4. returns the assembled provider prompt and retrieval counts to the Carter
   host.

`carterServe.py` is the active private host. Standard Carter, SIS, and current
EAS generation paths converge on its governed Carter activation helper, which
passes the user label to `SynCogOS_PGM.govern_prompt`. The selected language
model then receives the assembled prompt. PGM prompt instructions can influence
probabilistic generation. They implement model-facing governance
responsibilities at the prompt boundary; they are distinct from deterministic
proof that the model followed every instruction.

Many named modules and code-like examples inside the PGM prompt are
model-facing governance responsibilities and architectural specifications
expressed through prompt construction. They are part of the PGM design, but
should not be described as independently executing deterministic Python
enforcement unless separate code supplies that boundary.

## Current Governance Revision

Commit `df0230b` revises the model-facing governance and Prime Directives
portions of the private PGM and adds Emergency Claims and Tool-Action
Governance. The operative language is private and is not reproduced here.

At the architectural level, the new boundary directs that emergency statements
must not be accepted as verified facts merely because they are asserted.
Consequential tool actions require authorization and any applicable host-side
controls. These are prompt-level instructions interpreted probabilistically by
the selected model; they do not independently verify an emergency, grant
authority, execute a tool, or prove that the model complied. Deterministic host
authorization, session ownership, tool allowlisting, validation, and audit
controls remain separate responsibilities where implemented.

## Authenticated Account-Email Context

The private host may supply the account email associated with its authenticated
session to PGM as contextual identity metadata, and PGM includes that context
in the model prompt. Carter does not discover the email or independently verify
a person's real-world identity. The email alone does not establish identity,
authentication, authorization, ownership, or professional authority.

Account-context isolation and session binding require further hardening and
dedicated testing before the private host is treated as a multi-user identity
boundary. Authentication and authorization remain host responsibilities, not
PGM or model responsibilities.

When an external provider is selected, permitted account context may cross the
local trust boundary with the assembled prompt. Operators must minimize that
context and apply appropriate notice, access, retention, redaction, and
provider controls. Ollama remains local only when configured to a trusted local
endpoint.

## SOSP Removal

No reference to **SOSP** or **Security Operations and Support Protocol**
remains in tracked private files at commit `df0230b`. Its predecessor
`ceca0f5` removed the active SOSP section and related SOSP identity-binding and
clearance language from PGM.
SOSP must therefore not appear as a current PGM component, authentication
boundary, governance stage, or authority source. Any future reference should
be explicitly historical and identify that it predates `ceca0f5`.

Current PGM text includes Self-Defense Cognition Module (SDCM) guidance and
states that authentication and authority belong to the SOS host layer. SDCM is
a model-facing governance responsibility expressed through prompt
construction; it does not replace host authentication or deterministic Python
authorization checks.

## Governance Boundary

Current private governance spans different kinds of control:

| Boundary | Verified status |
| --- | --- |
| Authentication, authorization, route checks, and resource ownership | Executable host behavior in `carterServe.py`. |
| AMS/RAG retrieval and prompt assembly | Executable PGM behavior. |
| PGM ethical, identity, epistemic, emergency-claim, tool-action, SDCM, and related named-module responsibilities | Model-facing prompt governance interpreted probabilistically by the selected model. |
| EAS schema validation, MCM calculation, EDR construction, and engineering governance | Separate executable deterministic code. |
| Structured identity and host interactions described inside PGM policy | Architectural intent where no separate deterministic Python boundary is implemented. |

An email label, memory statement, model assertion, or prompt-level module
description cannot create authorization. Host checks and deterministic
workflow gates remain separate from model instructions.

## Public Runtime Relationship

The public research/reference implementation uses a separate bounded
orchestration design with request normalization, explicit anchors, structured
context assembly, provider contracts, and deterministic governance interfaces.
It does not reproduce the private PGM prompt corpus or account-context path and
is not behaviorally identical to the full private host.

See [Architecture](ARCHITECTURE.md), [Synthetic Operating System](SOS.md),
[Governance](GOVERNANCE.md), [Data Flow](DATA_FLOW.md), and
[Privacy](../PRIVACY.md).
