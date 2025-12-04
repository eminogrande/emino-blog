+++
title = "Why Nuri Chose a Stateless Passkey Architecture First — And How Lightning May Still Fit Later"
date = 2025-12-04T21:50:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "why-nuri-chose-a-stateless-passkey-architecture-first-and-ho"
+++


[image: image.png]
# Why Nuri Chose a Stateless Passkey Architecture First — And How Lightning
May Still Fit Later

Over the past months, we’ve had great conversations with the Breez team
about Spark, Nodeless, and the broader vision for Lightning-as-a-service.
Breez is one of the most thoughtful engineering teams in the Lightning
ecosystem, and their work has made Lightning accessible to developers who
don’t want to operate full nodes or manage liquidity themselves.

We were invited to join the Spark early-access program and the Q3/Q4 cohort
promotions. The outreach and support from Breez have been fantastic, and we
genuinely appreciate it.

After a lot of prototyping and research, however, Nuri chose a different
architectural direction for our first release. This post explains *why* we
took that path, how it relates to our core design principles, and how
Lightning may still play a role in the future.

---

## 1. Our Core Principle: Stateless Self-Custody

Most wallets labeled “self-custodial” still rely on persistent key storage,
either:

- encrypted on the device
- encrypted on a server
- or backed up through seed phrases

This introduces familiar risks:
device compromise, backup loss, server attacks, UX complexity, and
operational overhead.

Our goal with Nuri was to avoid **all** persistent private key storage,
while *increasing* security and improving recovery UX.

This led us to develop:

### 1.1 A Stateless Passkey Signer for Bitcoin
https://emino.app/posts/a-stateless-passkey-signer-for-bitcoin/

Instead of ever storing a private key, we use platform-secured passkeys
(FIDO2/WebAuthn) to deterministically derive ephemeral signing material
only when needed. No encrypted blobs. No seeds. No secrets at rest. Nothing
to exfiltrate.

### 1.2 A Passkey-Derived 2-of-2 Taproot Wallet
https://emino.app/posts/a-passkey-derived-2-of-2-taproot-wallet-architecture-elimina/

We extend the signer into a 2-of-2 Taproot multisig:

- one key is derived locally via passkey
- one key is derived remotely via an independent passkey
- neither side persists a long-term private key
- recovery is inherent to the passkey identity model

For Nuri, **statelessness is not an implementation detail — it is the
foundation**. All first-release architectures need to conform to this
principle.

---

## 2. Why Spark and Hosted Lightning Are Difficult to Combine With
Statelessness (Today)

Lightning requires durable state:

- channel commitments
- HTLC updates
- liquidity reservations
- revocation secrets
- channel backup material
- long-lived channel monitoring
- justice transaction protection

These requirements are fundamental to the Lightning protocol. They rely on
persistent, evolving state that must not be lost. This is at odds with
Nuri’s “no secrets, no state” philosophy.

We essentially had two options:

### Option A — Break our stateless model
Store channel state locally or remotely, weakening the guarantees we
designed Nuri around.

### Option B — Delegate long-lived state to a hosted node (e.g. Spark)
This is the Spark model:
user keeps signing keys, while the hosted infrastructure maintains channel
state, gossip, liquidity, and HTLCs.

Spark is well-designed, but adopting it early would mean building around a
dependency that doesn't fully match our architectural direction. We want
Nuri’s security model to be as minimal, deterministic, and platform-native
as possible before layering on stateful protocols.

---

## 3. Why We Chose Submarine Swaps First

Lightning functionality is still useful *without* maintaining a Lightning
node or channel state. Submarine swaps allow:

- receiving Lightning → settling on-chain
- sending on-chain → paying via Lightning
- without channel management
- without channel backups
- without persistent secrets
- without tying ourselves to a particular LSP or hosted service

This gives Nuri:

- Lightning interoperability
- architectural simplicity
- vendor independence
- full alignment with stateless signing principles

It’s the right step *before* committing to a more stateful integration like
hosted channels.

---

## 4. A Note to Breez — Why This Isn’t About You

This decision is not a critique of Breez or Spark.

In fact:

- Breez consistently ships some of the best engineering in the Lightning
space.
- Spark represents a clean, modern hosted-node architecture.
- Nodeless + Spark demonstrates a powerful developer experience.
- The Breez SDK dramatically simplifies Lightning for mobile apps.

Our divergence is purely due to **architecture**, not **quality**.

Lightning today requires persistent state. Nuri today is built on stateless
primitives. Once our foundation stabilizes, we can revisit options like
Spark or hybrid models that respect our stateless guarantees.

The door remains open.

---

## 5. What Nuri Is Shipping Now

Nuri recently passed Apple review (TestFlight: https://testflight.nuri.com)
and our initial feature set focuses on:

- **Buy Bitcoin with no KYC up to €700** using Apple Pay (via Mercuryo)
- **Self-custodial Visa debit card** with GnosisPay
- **IBAN with instant SEPA on/off-ramp** from Monerium
- **Stateless passkey-based Bitcoin signing**
- **2-of-2 Taproot architecture with no stored private keys**
- **Zero secret storage—client or server**
- **Cross-platform Expo app (iOS, Android, Web)**
- **All components will be fully open source**, including the signer and
the wallet UI

Our priority is to perfect the stateless model first. Lightning will follow
once it can integrate cleanly with that architecture.

---

## 6. The Future: Can Lightning Become Stateless?

This is an open research area we care about deeply. Promising directions
include:

- Taproot-based channel designs
- eltoo-like update schemes
- state commitment trees
- ephemeral channel construction
- passkey-driven Lightning signing roles
- multi-provider hosted channels without lock-in

As these areas evolve, we expect Lightning to become more compatible with
stateless client models. When that happens, Spark or similar offerings may
become a natural fit.

---

## 7. Thank You, Breez

To the Breez team:

Thank you for reaching out repeatedly, inviting us into Spark and your
cohort programs, and for being open to conversation. Your work is critical
to Lightning’s future. Although our architectural paths diverge for now, we
have a tremendous amount of respect for what you are building.

When our stateless primitives are fully matured, Lightning integration will
return to the roadmap — and Spark will absolutely remain under
consideration.

⚡️

---

![image](/media/why-nuri-chose-a-stateless-passkey-architecture-first-and-ho/image.png)

---
*Post created via email from emin@nuri.com*
