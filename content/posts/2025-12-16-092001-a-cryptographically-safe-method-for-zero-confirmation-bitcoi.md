+++
title = "A Cryptographically Safe Method for Zero-Confirmation Bitcoin Acceptance"
date = 2025-12-16T09:20:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "a-cryptographically-safe-method-for-zero-confirmation-bitcoi"
markup = "markdown"
body_format = "markdown"
+++

![](/media/a-cryptographically-safe-method-for-zero-confirmation-bitcoi/cover.jpg)

## Abstract

Bitcoin transactions are not final until confirmed in a block. Any
transaction spending a given UTXO can be replaced by another valid
transaction spending the same inputs until one is confirmed. This
makes generic zero-confirmation acceptance unsafe.

This document describes a construction that allows a service to safely
accept and act upon a zero-confirmation Bitcoin transaction, in the
sense that the payer cannot create a conflicting valid transaction
during a defined window. The construction relies on enforcing signing
authority at the UTXO level and does not depend on mempool behavior or
miner policy.

---

## Problem Statement

Let a UTXO `U` be spendable by a user.

A zero-confirmation transaction `T` spending `U` is unsafe if the user
can also construct a different transaction `T'` that spends `U` and
have it confirmed instead of `T`.

This remains true regardless of:
- transaction fees,
- Replace-by-Fee signaling,
- mempool propagation,
- script structure inside `T`.

Therefore, zero-confirmation safety requires preventing the existence
of any alternative valid spend of `U`.

---

## Design Principle

A conflicting transaction can only exist if the payer can
independently produce a valid spend.

The necessary and sufficient condition for safe zero-confirmation acceptance is:

> During the acceptance window, the payer must be unable to create any valid transaction spending the relevant UTXOs without the service’s participation.

This condition must be enforced cryptographically at the UTXO level.

---

## UTXO Construction

Funds are held in a Taproot output with two spending paths.

### Cooperative Path (Immediate)

- Requires signatures from:
  - the user, and
  - the service’s co-signing key
- No timelock
- Used for all normal spends

### Unilateral Recovery Path (Delayed)

- Requires only the user’s signature
- Enforced by `OP_CHECKSEQUENCEVERIFY`
- Becomes valid after `N` blocks

This structure ensures:
- the service does not have custody,
- the user can recover funds unilaterally after the delay,
- no unilateral spend is possible before the delay expires.

---

## Zero-Confirmation Acceptance Mechanism

Let `U` be an output using the above structure.

1. The user constructs a transaction `T` spending `U`.
2. The transaction is submitted to the service for co-signing.
3. The service verifies policy conditions (destination, amount, fee).
4. The service signs `T` exactly once for each outpoint in `U`.
5. The transaction is broadcast.

At this point:
- `T` is valid,
- no other valid transaction spending `U` can exist,
- mempool behavior is irrelevant.

The transaction may be treated as authorized immediately, despite
being unconfirmed.

---

## Co-Signer Requirements

The co-signing service must enforce the following invariants:

1. **One signature per outpoint**
   - Each UTXO may be signed at most once
   - Enforcement must use durable state

2. **Atomic sign-and-lock**
   - Signing and state recording must be atomic
   - Concurrent requests must not result in multiple signatures

3. **Transaction-level commitment**
   - The signature must commit to the full transaction digest
   - No intent-based signing is permitted

4. **Reorg awareness**
   - State must not be released solely based on a single confirmation
   - Outpoints must remain locked until reorg risk is acceptable

Failure to meet any of these conditions invalidates the safety guarantee.

---

## Timing Considerations

The unilateral recovery path is enforced by a relative timelock
(`OP_CHECKSEQUENCEVERIFY`) measured from the confirmation of the
parent output.

Consequently:
- before confirmation, only the cooperative path is valid,
- after confirmation, the delay must be long enough to allow the
cooperative spend to confirm under adverse fee conditions.

The service must ensure that the cooperative transaction is likely to
confirm before the recovery path becomes valid, or accept the
associated economic risk.

---

## Application to Lightning Swaps

In a Bitcoin-to-Lightning swap:

- the cooperative on-chain spend serves as authorization,
- the Lightning payment may be initiated immediately after co-signing,
- on-chain confirmation serves as settlement.

Because no conflicting spend can exist during the cooperative window,
triggering the Lightning payment at zero confirmations does not expose
the service to payer double-spend risk.

---

## Limitations

This construction eliminates payer double-spend risk only.

It does not eliminate:
- co-signer compromise,
- service availability failures,
- transaction confirmation delays,
- miner censorship.

These risks must be addressed operationally.

---

## Conclusion

Safe zero-confirmation acceptance in Bitcoin is only possible by
removing the payer’s ability to create conflicting valid transactions.

This requires:
- mandatory co-signing at the UTXO level,
- strict enforcement of one-time signing per outpoint,
- a delayed unilateral recovery path for the user.

Any approach that does not enforce these conditions cannot provide
cryptographic zero-confirmation safety.

---
*Post created via email from emin@nuri.com*
