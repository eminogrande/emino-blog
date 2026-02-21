+++
title = "Agentic Wallets & Passkey PRF: The Nuri.com Security Architecture"
date = 2026-02-10T08:00:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "agentic-wallets-passkey-prf-the-nuri-com-security-architectu"
markup = "markdown"
body_format = "markdown"
+++

# Agentic Wallets & Passkey PRF: The Nuri.com Security Architecture

## Executive Summary
Traditional wallet security usually forces a trade-off between
self-custody (seed phrases) and convenience (custodial). By leveraging
the **WebAuthn PRF (Pseudo-Random Function) extension**, we have
implemented a third way at **nuri.com**: A hardware-backed,
deterministic, multi-sig wallet architecture designed specifically for
the era of AI Agents.

---

## 1. The PRF Revolution: Hardware as the Seed
The core innovation lies in moving away from stored secrets. Instead
of a master password or a stored JSON file, we use the Passkey PRF
extension to derive entropy directly from the authenticator (e.g.,
TouchID, FaceID, or YubiKey).

* **Deterministic Output:** Every time the user authenticates, the PRF
extension produces the exact same output for a given input/salt.
* **The "Zero-Storage" Model:** $Seed =
\text{HMAC-SHA256}(\text{AuthenticatorSecret}, \text{Salt})$
    Because we can re-derive this $Seed$ at any time, the private keys
are generated on-the-fly and **zeroized (wiped)** immediately after
the signature is produced.

## 2. Decaying Multi-Sig: The Ultimate Fail-Safe
To balance security with availability, we utilize a **Decaying
Multi-Signature** script.
* **Active State:** Requires 2-of-2 signatures (The PRF-derived key +
a Service-backed key).
* **Decay Mechanism:** If the service (Relying Party) becomes
unavailable or the domain is lost, a time-lock (CheckSequenceVerify)
allows the wallet to transition into a 1-of-1 state.
* **Outcome:** The user is never locked out of their funds by a
service provider, yet enjoys the security of co-signing during normal
operations.

## 3. The "Agentic Wallet" Paradigm
As AI agents begin to handle on-chain logic, the bottleneck becomes
**Authorization vs. Execution**.

### How it works with Agents:
1.  **Preparation:** An AI Agent monitors the chain and prepares a
complex transaction (e.g., "Rebalance my DeFi positions if gas is
low").
2.  **Orchestration:** The Agent handles all the "legwork" and
presents a ready-to-sign payload to the user.
3.  **Biometric Co-signing:** Because the private key requires a
biometric trigger via the Passkey PRF, the Agent **cannot** spend
funds autonomously.
4.  **Security:** This creates a hardware-bound guardrail. The Agent
is the "pilot," but the User’s thumbprint is the "ignition key."

## 4. Cross-Chain Versatility
While many Passkey implementations focus solely on EVM (via ERC-4337),
our setup at **nuri.com** is chain-agnostic. By deriving a master
seed, we support:
* **Bitcoin:** Native SegWit/Taproot transactions via deterministic
BIP32 derivation.
* **EVM:** Full compatibility with Ethereum-based chains and Account
Abstraction.

## 5. Conclusion: Why this matters
This setup moves us toward a "Secretless" future. There is no seed
phrase to lose, no master password to phish, and no service provider
that can freeze your funds indefinitely. By open-sourcing this
orchestration logic, we aim to provide the foundational layer for
secure, human-in-the-loop Agentic Wallets.

![image](/media/agentic-wallets-passkey-prf-the-nuri-com-security-architectu/image.png)

---
*Post created via email from emin@nuri.com*
