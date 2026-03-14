+++
title = "Nuri Wallet: A Stateless MuSig2 Bitcoin Wallet with Decaying Multisig Recovery"
date = 2025-12-08T21:00:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "nuri-wallet-a-stateless-musig2-bitcoin-wallet-with-decaying-"
markup = "markdown"
body_format = "markdown"
image =  "/media/nuri-wallet-a-stateless-musig2-bitcoin-wallet-with-decaying-/cover.jpg"
+++

![](/media/nuri-wallet-a-stateless-musig2-bitcoin-wallet-with-decaying-/cover.jpg)

Work in Progress. Document written by Opus 4.5

## Technical Design Document

---

## Executive Summary

Nuri Wallet is a next-generation Bitcoin wallet that combines **MuSig2
Schnorr signatures**, **stateless key derivation via WebAuthn PRF**,
**NFC hardware wallet integration**, and **server-assisted two-factor
authentication** into a unified security architecture. The design
prioritizes both security and recoverability through a **decaying
multisig** mechanism that ensures users can always recover their
funds, even if one or more signing components become unavailable.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Architecture Overview](#architecture-overview)
3. [Key Components](#key-components)
   - [Stateless Passkey Wallet](#stateless-passkey-wallet)
   - [Hardware Wallet (NFC SatochipSigning
Device)](#hardware-wallet-nfc-satscard-signing-device)
   - [Stateless Server](#stateless-server)
4. [MuSig2 Protocol Integration](#musig2-protocol-integration)
5. [Wallet Configurations](#wallet-configurations)
   - [2-of-2 Configuration](#2-of-2-configuration)
   - [2-of-3 Configuration](#2-of-3-configuration)
6. [Decaying Multisig with CSV Timelocks](#decaying-multisig-with-csv-timelocks)
7. [Security Analysis](#security-analysis)
8. [Recovery Scenarios](#recovery-scenarios)
9. [Comparison with Existing Solutions](#comparison-with-existing-solutions)
10. [Implementation Considerations](#implementation-considerations)

---

## Introduction

Traditional Bitcoin wallets face a fundamental tension between
**security** and **usability**. Single-signature wallets are
vulnerable to key theft, while multisig wallets can lock users out of
their funds if keys are lost. Nuri Wallet resolves this tension
through an innovative combination of:

- **Stateless key derivation**: No persistent key storage means no
keys to steal from rest
- **MuSig2 aggregated signatures**: Multiple parties contribute to a
single Schnorr signature, maintaining privacy and reducing transaction
fees
- **Decaying timelocks**: Graduated recovery options that balance
security against lockout risk
- **Hardware wallet integration**: Optional cold storage for maximum security

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           NURI WALLET ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │   PASSKEY KEY    │  │  HARDWARE KEY    │  │   SERVER KEY     │          │
│  │   (Stateless)    │  │  (NFC Satochip)  │  │   (Stateless)    │          │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────────┤          │
│  │ WebAuthn PRF     │  │ Secure Element   │  │ HSM/Secure       │          │
│  │ Extension        │  │ on NFC Card      │  │ Element          │          │
│  │                  │  │                  │  │                  │          │
│  │ key = PRF(salt)  │  │ Private key      │  │ key = f(user_id, │          │
│  │                  │  │ never leaves     │  │        entropy)  │          │
│  │ No key storage   │  │ the chip         │  │                  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           │    MuSig2 Partial   │    MuSig2 Partial   │                     │
│           │    Signature        │    Signature        │                     │
│           │                     │                     │                     │
│           └──────────┬──────────┴──────────┬──────────┘                     │
│                      │                     │                                │
│                      ▼                     ▼                                │
│           ┌─────────────────────────────────────────┐                       │
│           │         MuSig2 SIGNATURE AGGREGATION    │                       │
│           │                                         │                       │
│           │  2-of-2: Passkey + Server               │                       │
│           │  2-of-3: Any 2 of {Passkey, HW, Server} │                       │
│           └─────────────────────────────────────────┘                       │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    DECAYING TIMELOCK STRUCTURE                       │   │
│  │                                                                      │   │
│  │   T=0                    T=10,000 blocks              T=52,560       │   │
│  │    │                          │                       blocks         │   │
│  │    ▼                          ▼                          ▼           │   │
│  │  ┌────────────────────┬───────────────────────┬─────────────────┐   │   │
│  │  │  NORMAL OPERATION  │  RECOVERY MODE        │  EMERGENCY EXIT │   │   │
│  │  │  2-of-2 or 2-of-3  │  Passkey + HW         │  Passkey only   │   │
│  │  │  (Server active)   │  (Server unavailable) │  (CSV expired)  │   │
│  │  └────────────────────┴───────────────────────┴─────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### Stateless Passkey Wallet

The passkey-based key is the cornerstone of Nuri's user experience. It
leverages the **WebAuthn PRF (Pseudo-Random Function) extension** to
derive cryptographic keys without ever storing them.

#### How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    PASSKEY KEY DERIVATION                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   User authenticates with passkey (biometric/PIN)               │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │         WebAuthn Authenticator          │                  │
│   │    (Platform or Roaming Authenticator)  │                  │
│   └─────────────────────────────────────────┘                  │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │           PRF Extension                 │                  │
│   │                                         │                  │
│   │   secret = HMAC-SHA256(device_secret,   │                  │
│   │                        salt || rpId)    │                  │
│   └─────────────────────────────────────────┘                  │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │      Bitcoin Key Derivation             │                  │
│   │                                         │                  │
│   │   private_key = HKDF(secret,            │                  │
│   │                      "nuri-bitcoin",    │                  │
│   │                      derivation_path)   │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Security Properties

| Property | Description |
|----------|-------------|
| **Stateless** | No private keys stored on device; derived on-demand |
| **Phishing Resistant** | WebAuthn binds credentials to origin |
| **Hardware-Backed** | PRF secret stored in device secure element |
| **Biometric Protected** | User presence verified via fingerprint/face |

#### Key Derivation Formula

Given:
- $s$ = device master secret (in secure element)
- $\text{salt}$ = application-specific salt
- $\text{rpId}$ = relying party identifier

The PRF output is:

$$\text{prf\_output} = \text{HMAC-SHA256}(s, \text{salt} \| \text{rpId})$$

The Bitcoin private key is then derived as:

$$k_{\text{passkey}} = \text{HKDF-SHA256}(\text{prf\_output},
\text{"nuri-btc-v1"}, \text{path})$$

---

### Hardware Wallet (NFC Satochip Signing Device)

The hardware wallet component uses an **NFC-based secure element
card** (similar to Satochip or SatSigner) that performs **MuSig2
partial signing** without ever exposing its private key.

#### Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                  NFC HARDWARE WALLET                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────┐                                      │
│   │   Secure Element    │                                      │
│   │   (JavaCard/etc)    │                                      │
│   ├─────────────────────┤                                      │
│   │ • Private key       │  ◄── Never leaves the chip           │
│   │   generation        │                                      │
│   │ • MuSig2 nonce      │                                      │
│   │   generation        │                                      │
│   │ • Partial signature │                                      │
│   │   creation          │                                      │
│   │ • Public key export │                                      │
│   └─────────────────────┘                                      │
│            ▲                                                    │
│            │ NFC                                                │
│            ▼                                                    │
│   ┌─────────────────────┐                                      │
│   │   Mobile Device     │                                      │
│   │   (Nuri App)        │                                      │
│   └─────────────────────┘                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### MuSig2 Signing Flow

1. **Nonce Commitment Round**: Card generates random nonce
$R_{\text{hw}}$ and provides commitment
2. **Nonce Exchange**: All parties exchange nonce commitments, then
reveal nonces
3. **Partial Signing**: Card computes partial signature without
revealing private key
4. **Aggregation**: Partial signatures combined into final Schnorr signature

---

### Stateless Server

The server acts as a **2FA-protected co-signer** that adds entropy and
provides an additional security layer without introducing custody
risk.

#### Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                    STATELESS SERVER                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────────────────────────────────┐                  │
│   │         Hardware Security Module        │                  │
│   │              (HSM)                       │                  │
│   ├─────────────────────────────────────────┤                  │
│   │ • Master seed (never exported)          │                  │
│   │ • Deterministic key derivation          │                  │
│   │ • Rate limiting                         │                  │
│   │ • Audit logging                         │                  │
│   └─────────────────────────────────────────┘                  │
│                          │                                      │
│                          ▼                                      │
│   ┌─────────────────────────────────────────┐                  │
│   │      Key Derivation Function            │                  │
│   │                                         │                  │
│   │   k_server = KDF(master_seed,           │                  │
│   │                  user_id,               │                  │
│   │                  wallet_id,             │                  │
│   │                  key_index)             │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Properties:                                                   │
│   • No private keys stored in database                         │
│   • Keys derived on-demand from HSM                            │
│   • 2FA required before signing                                │
│   • Server breach doesn't compromise keys                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Server Key Derivation

The server derives user-specific keys deterministically:

$$k_{\text{server}} = \text{HKDF}(k_{\text{master}}, \text{user\_id}
\| \text{wallet\_id} \| \text{index})$$

Where $k_{\text{master}}$ is stored in the HSM and never exported.

---

## MuSig2 Protocol Integration

MuSig2 is a **multi-signature scheme** that produces a single
aggregated Schnorr signature indistinguishable from a regular
signature. This provides both **privacy** (observers can't tell it's
multisig) and **efficiency** (smaller transactions, lower fees).

### MuSig2 Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                     MuSig2 PROTOCOL                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   SETUP PHASE (one-time)                                        │
│   ──────────────────────                                        │
│                                                                 │
│   Each party i has:                                             │
│   • Private key: xᵢ                                             │
│   • Public key:  Pᵢ = xᵢ · G                                    │
│                                                                 │
│   Aggregated public key:                                        │
│   P = Σᵢ (aᵢ · Pᵢ)                                              │
│   where aᵢ = H(L, Pᵢ) and L = {P₁, P₂, ...}                     │
│                                                                 │
│   SIGNING PHASE (per transaction)                               │
│   ───────────────────────────────                               │
│                                                                 │
│   Round 1: Nonce Generation                                     │
│   ┌─────────┐  ┌─────────┐  ┌─────────┐                        │
│   │ Party 1 │  │ Party 2 │  │ Party 3 │                        │
│   │ r₁ → R₁ │  │ r₂ → R₂ │  │ r₃ → R₃ │                        │
│   └────┬────┘  └────┬────┘  └────┬────┘                        │
│        │            │            │                              │
│        └────────────┼────────────┘                              │
│                     ▼                                           │
│              Exchange Rᵢ values                                 │
│                     │                                           │
│                     ▼                                           │
│   Round 2: Partial Signatures                                   │
│                                                                 │
│   R = Σᵢ Rᵢ  (aggregated nonce)                                 │
│   c = H(R, P, m)  (challenge)                                   │
│                                                                 │
│   Each party computes:                                          │
│   sᵢ = rᵢ + c · aᵢ · xᵢ                                         │
│                                                                 │
│   Final signature:                                              │
│   s = Σᵢ sᵢ                                                     │
│   σ = (R, s)                                                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why MuSig2 for Nuri?

| Benefit | Description |
|---------|-------------|
| **Privacy** | Aggregated signature looks like single-sig on-chain |
| **Efficiency** | One signature regardless of number of signers |
| **Taproot Native** | Designed for Bitcoin's Schnorr/Taproot upgrade |
| **Non-Interactive** | Only 2 rounds of communication needed |

---

## Wallet Configurations

### 2-of-2 Configuration

The basic configuration requires both the **passkey** and **server**
to sign transactions.

```
┌─────────────────────────────────────────────────────────────────┐
│                    2-of-2 CONFIGURATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   NORMAL OPERATION                                              │
│   ────────────────                                              │
│                                                                 │
│   ┌───────────┐         ┌───────────┐                          │
│   │  Passkey  │────────▶│  Server   │                          │
│   │   Key     │  2FA    │   Key     │                          │
│   └─────┬─────┘ verify  └─────┬─────┘                          │
│         │                     │                                 │
│         │    MuSig2          │                                 │
│         └──────────┬─────────┘                                 │
│                    ▼                                            │
│              ┌──────────┐                                       │
│              │ Combined │                                       │
│              │Signature │                                       │
│              └──────────┘                                       │
│                                                                 │
│   RECOVERY (Server Unavailable)                                 │
│   ─────────────────────────────                                 │
│                                                                 │
│   After CSV timelock expires (~1 year):                         │
│                                                                 │
│   ┌───────────┐                                                │
│   │  Passkey  │──────────────▶ Spend with single signature     │
│   │   Key     │                (CSV exit path)                 │
│   └───────────┘                                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Transaction Structure (Taproot)

```
Output Script (P2TR):
┌─────────────────────────────────────────────────────────────────┐
│  OP_1 <aggregated_pubkey>                                       │
└─────────────────────────────────────────────────────────────────┘

Taproot Tree:
┌─────────────────────────────────────────────────────────────────┐
│                         Internal Key                            │
│                    (MuSig2: Passkey + Server)                   │
│                              │                                  │
│              ┌───────────────┴───────────────┐                  │
│              │                               │                  │
│        ┌─────▼─────┐                  ┌──────▼──────┐           │
│        │  Leaf 1   │                  │   Leaf 2    │           │
│        │  (empty)  │                  │  CSV Exit   │           │
│        │           │                  │ <pk_passkey>│           │
│        │           │                  │ CHECKSIG    │           │
│        │           │                  │ <52560>     │           │
│        │           │                  │ CSV         │           │
│        └───────────┘                  └─────────────┘           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### 2-of-3 Configuration

The enhanced configuration adds a **hardware wallet** for additional
security and recovery options.

```
┌─────────────────────────────────────────────────────────────────┐
│                    2-of-3 CONFIGURATION                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   THREE SIGNING KEYS                                            │
│   ──────────────────                                            │
│                                                                 │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐              │
│   │  Passkey  │    │ Hardware  │    │  Server   │              │
│   │   (Hot)   │    │  Wallet   │    │  (2FA)    │              │
│   │           │    │  (Cold)   │    │           │              │
│   └─────┬─────┘    └─────┬─────┘    └─────┬─────┘              │
│         │                │                │                     │
│         └────────┬───────┴───────┬────────┘                     │
│                  │               │                              │
│                  ▼               ▼                              │
│         ┌──────────────────────────────┐                        │
│         │   ANY 2-of-3 can sign        │                        │
│         │                              │                        │
│         │   • Passkey + Server (daily) │                        │
│         │   • Passkey + HW (recovery)  │                        │
│         │   • Server + HW (if needed)  │                        │
│         └──────────────────────────────┘                        │
│                                                                 │
│   SIGNING SCENARIOS                                             │
│   ─────────────────                                             │
│                                                                 │
│   Scenario 1: Normal (Passkey + Server)                         │
│   ┌─────────┐  2FA  ┌─────────┐                                │
│   │ Passkey ├──────▶│ Server  │────▶ ✓ Transaction             │
│   └─────────┘       └─────────┘                                │
│                                                                 │
│   Scenario 2: Server Down (Passkey + Hardware)                  │
│   ┌─────────┐  NFC  ┌─────────┐                                │
│   │ Passkey ├──────▶│   HW    │────▶ ✓ Transaction             │
│   └─────────┘       └─────────┘      (No waiting!)             │
│                                                                 │
│   Scenario 3: Passkey Lost (Hardware + Server)                  │
│   ┌─────────┐       ┌─────────┐                                │
│   │   HW    ├──────▶│ Server  │────▶ ✓ Transaction             │
│   └─────────┘       └─────────┘                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Taproot Structure for 2-of-3

```
Taproot Tree (2-of-3):
┌─────────────────────────────────────────────────────────────────┐
│                         Internal Key                            │
│              (MuSig2: Passkey + Server - default path)          │
│                              │                                  │
│      ┌───────────────────────┼───────────────────────┐          │
│      │                       │                       │          │
│ ┌────▼────┐           ┌──────▼──────┐         ┌──────▼──────┐   │
│ │ Leaf 1  │           │   Leaf 2    │         │   Leaf 3    │   │
│ │Passkey+ │           │ Passkey+    │         │  CSV Exit   │   │
│ │  HW     │           │  Server     │         │<pk_passkey> │   │
│ │(MuSig2) │           │ (redundant) │         │ CHECKSIG    │   │
│ │         │           │             │         │ <52560> CSV │   │
│ └─────────┘           └─────────────┘         └─────────────┘   │
│                                                                 │
│ Note: Server+HW combination handled via Leaf 2 alternative      │
│       or additional leaf as needed                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Decaying Multisig with CSV Timelocks

The **decaying multisig** pattern ensures that users can always
recover their funds, with security guarantees that gracefully degrade
over time.

### How CSV (CheckSequenceVerify) Works

CSV enforces a **relative timelock** measured in blocks since the UTXO
was created:

$$\text{spendable\_height} = \text{confirmation\_height} + \text{csv\_blocks}$$

For Nuri Wallet:
- **Normal operation**: 2-of-2 or 2-of-3 MuSig2 required
- **After ~70 days** (10,000 blocks): Alternative recovery paths activate
- **After ~1 year** (52,560 blocks): Single-key emergency exit available

### Timelock Visualization

```
┌─────────────────────────────────────────────────────────────────┐
│                    DECAYING SECURITY MODEL                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Security                                                       │
│  Level                                                          │
│    ▲                                                            │
│    │                                                            │
│  3 ┤ ████████████████████┐                                      │
│    │                     │                                      │
│  2 ┤                     └───────────────────┐   2-of-3 config  │
│    │                                         │   (HW available) │
│    │                                         │                  │
│  1 ┤                                         └─────────────     │
│    │                                                            │
│    └────────────────────────────────────────────────────▶       │
│         T=0            T=10,000         T=52,560      Time      │
│         │              blocks           blocks        (blocks)  │
│         │              (~70 days)       (~1 year)               │
│         │                 │                │                    │
│         ▼                 ▼                ▼                    │
│   ┌──────────┐     ┌──────────────┐  ┌──────────────┐          │
│   │ Maximum  │     │ HW Recovery  │  │  Emergency   │          │
│   │ Security │     │  Available   │  │    Exit      │          │
│   │  2FA +   │     │ No server    │  │  Passkey     │          │
│   │ Passkey  │     │   needed     │  │    only      │          │
│   └──────────┘     └──────────────┘  └──────────────┘          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Script Structure

**CSV Exit Script (simplified):**

```
OP_IF
    // Normal spending path: requires aggregated MuSig2 signature
    <aggregated_pubkey>
    OP_CHECKSIG
OP_ELSE
    // Emergency exit: after timelock, passkey alone can spend
    <52560>           // ~1 year in blocks
    OP_CHECKSEQUENCEVERIFY
    OP_DROP
    <passkey_pubkey>
    OP_CHECKSIG
OP_ENDIF
```

### Re-locking Mechanism

To maintain maximum security, users should periodically "refresh" their UTXOs:

```
┌─────────────────────────────────────────────────────────────────┐
│                    UTXO REFRESH CYCLE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Initial Deposit          After 11 months         Re-deposit  │
│        │                        │                       │       │
│        ▼                        ▼                       ▼       │
│   ┌─────────┐              ┌─────────┐             ┌─────────┐ │
│   │  UTXO   │   Time       │  UTXO   │   Self-    │  UTXO   │ │
│   │  CSV=0  │  ─────▶      │CSV=47520│   send     │  CSV=0  │ │
│   │         │              │ (aging) │  ─────▶    │ (fresh) │ │
│   └─────────┘              └─────────┘             └─────────┘ │
│                                                                 │
│   Security: MAX            Security: Degrading    Security: MAX│
│                                                                 │
│   Wallet prompts user when UTXOs approach timelock expiry      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Security Analysis

### Threat Model

| Threat | Mitigation |
|--------|------------|
| **Device theft** | Passkey protected by biometrics; key derived on-demand |
| **Server compromise** | Server keys in HSM; stateless derivation;
server alone cannot spend |
| **Phishing** | WebAuthn origin binding prevents credential theft |
| **Man-in-the-middle** | MuSig2 nonce protocol prevents signature forgery |
| **Server disappearance** | CSV timelock enables recovery; HW wallet
provides immediate alternative |
| **Hardware wallet loss** | 2-of-3 allows recovery with passkey + server |
| **Passkey loss** | 2-of-3 allows recovery with HW + server |

### Security Levels by Configuration

```
┌─────────────────────────────────────────────────────────────────┐
│                SECURITY COMPARISON                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    2-of-2           2-of-3                      │
│                    ──────           ──────                      │
│                                                                 │
│   Keys Required      2                2                         │
│   to Spend                                                      │
│                                                                 │
│   Single Point       Passkey         None                       │
│   of Failure         (for CSV exit)  (any 2 keys work)          │
│                                                                 │
│   Server Down        Wait ~1 year    Use Passkey + HW           │
│   Recovery                           (immediate)                │
│                                                                 │
│   Passkey Lost       Funds locked    Use Server + HW            │
│   Recovery           (CSV doesn't    (immediate)                │
│                      help here!)                                │
│                                                                 │
│   Best For           Simplicity,     Maximum security,          │
│                      casual users    significant holdings       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Attack Scenarios

#### Scenario 1: Attacker Compromises Server

```
Attacker obtains: Server signing capability
Attacker needs:   Passkey authentication OR Hardware wallet

Result: ❌ Cannot steal funds (missing second key)
        ⚠️  Can potentially DoS by refusing to sign
        ✅ User recovers via CSV exit or HW wallet
```

#### Scenario 2: Attacker Steals Phone

```
Attacker obtains: Physical device
Attacker needs:   Biometric/PIN to unlock passkey
                  PLUS 2FA to authorize server signing

Result: ❌ Cannot steal funds (passkey protected by biometrics)
        ✅ Keys never stored on device (stateless)
```

#### Scenario 3: Attacker Compromises Both Passkey AND Server

```
Attacker obtains: Passkey credential + Server access
Result: ⚠️  Can steal funds in 2-of-2 config
        ✅ 2-of-3 config: HW wallet still required
```

---

## Recovery Scenarios

### Complete Recovery Matrix

| Scenario | 2-of-2 Config | 2-of-3 Config |
|----------|---------------|---------------|
| **Lost phone (passkey)** | Wait for CSV (~1 year), then... ❌ still
can't spend! | Server + HW ✅ |
| **Server goes offline** | Wait for CSV (~1 year) ✅ | Passkey + HW ✅
(immediate) |
| **Lost hardware wallet** | N/A (not in config) | Passkey + Server ✅ |
| **Lost phone + server down** | ❌ Funds lost | HW can spend after
CSV? (design decision) |
| **Lost HW + server down** | Wait for CSV ✅ | Wait for CSV ✅ |

### Recovery Flow: Server Unavailable (2-of-3)

```
┌─────────────────────────────────────────────────────────────────┐
│          RECOVERY: SERVER UNAVAILABLE (2-of-3)                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Step 1: Detect server unavailability                          │
│   ┌─────────────────────────────────────────┐                  │
│   │ App: "Server unreachable. Use hardware  │                  │
│   │       wallet for recovery signing?"     │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 2: Authenticate with passkey                             │
│   ┌─────────────────────────────────────────┐                  │
│   │ User: [Biometric authentication]        │                  │
│   │ App:  Derives passkey private key       │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 3: Tap NFC hardware wallet                               │
│   ┌─────────────────────────────────────────┐                  │
│   │ App: "Tap your Nuri Card to sign"       │                  │
│   │                                         │                  │
│   │        ┌───────────┐                    │                  │
│   │        │  📱 ←→ 💳 │  NFC               │                  │
│   │        └───────────┘                    │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 4: MuSig2 signing between Passkey + HW                   │
│   ┌─────────────────────────────────────────┐                  │
│   │ Passkey partial sig + HW partial sig    │                  │
│   │              ↓                          │                  │
│   │    Aggregated Schnorr signature         │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 5: Broadcast transaction                                 │
│   ┌─────────────────────────────────────────┐                  │
│   │ Transaction broadcast to Bitcoin network│                  │
│   │ ✅ Funds recovered without server       │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Recovery Flow: CSV Emergency Exit (2-of-2)

```
┌─────────────────────────────────────────────────────────────────┐
│              RECOVERY: CSV EMERGENCY EXIT                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Prerequisites:                                                │
│   • Server has been unavailable for extended period             │
│   • UTXO age > 52,560 blocks (~1 year)                          │
│   • User still has passkey access                               │
│                                                                 │
│   Step 1: Check UTXO eligibility                                │
│   ┌─────────────────────────────────────────┐                  │
│   │ App scans UTXOs for CSV-eligible funds  │                  │
│   │                                         │                  │
│   │ UTXO 1: 0.5 BTC  - Age: 55,000 blocks ✅│                  │
│   │ UTXO 2: 0.3 BTC  - Age: 40,000 blocks ❌│                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 2: Construct CSV spending transaction                    │
│   ┌─────────────────────────────────────────┐                  │
│   │ Input: UTXO with nSequence = 52,560     │                  │
│   │ Witness: <passkey_signature> <csv_script>│                  │
│   │ Output: New address controlled by user  │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 3: Sign with passkey only                                │
│   ┌─────────────────────────────────────────┐                  │
│   │ No server needed - single signature     │                  │
│   │ sufficient for CSV exit path            │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
│   Step 4: Broadcast and confirm                                 │
│   ┌─────────────────────────────────────────┐                  │
│   │ Transaction valid because:              │                  │
│   │ • CSV timelock satisfied                │                  │
│   │ • Valid passkey signature provided      │                  │
│   │ ✅ Funds recovered!                     │                  │
│   └─────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Comparison with Existing Solutions

### Nuri vs. Blockstream Green

| Feature | Blockstream Green | Nuri Wallet |
|---------|-------------------|-------------|
| **Signature Scheme** | ECDSA multisig | MuSig2 Schnorr |
| **On-chain Footprint** | Visible multisig | Single-sig appearance |
| **Client Key Storage** | Encrypted on device | Stateless (PRF-derived) |
| **Server Key Storage** | Traditional HSM | Stateless HSM derivation |
| **Recovery (2-of-2)** | CSV timelock | CSV timelock |
| **Recovery (2-of-3)** | Backup key phrase | Hardware wallet |
| **Taproot Support** | Limited | Native |

### Nuri vs. Traditional Hardware Wallets

| Feature | Ledger/Trezor | Nuri Wallet |
|---------|---------------|-------------|
| **Form Factor** | Dedicated device | Passkey + NFC card |
| **Daily Transactions** | Device required | Passkey only (server 2FA) |
| **High-Value Transactions** | Same as daily | Can require HW card |
| **Loss Recovery** | Seed phrase | Multiple paths (CSV, 2-of-3) |
| **Theft Risk** | Seed phrase exposure | No seed phrase needed |

### Nuri vs. Custodial Solutions

| Feature | Custodial Exchange | Nuri Wallet |
|---------|-------------------|-------------|
| **Key Control** | Exchange holds keys | User holds all keys |
| **Counterparty Risk** | High | None |
| **Regulatory Risk** | Subject to seizure | Self-sovereign |
| **Recovery** | Account recovery | CSV + multisig |
| **Privacy** | KYC required | No KYC for self-custody |

---

## Implementation Considerations

### WebAuthn PRF Browser Support

```
┌─────────────────────────────────────────────────────────────────┐
│                 WEBAUTHN PRF SUPPORT STATUS                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Browser/Platform          PRF Support    Notes                │
│   ────────────────          ───────────    ─────                │
│   Chrome (Desktop)          ✅ Yes         Windows Hello, etc.  │
│   Chrome (Android)          ✅ Yes         Fingerprint/PIN      │
│   Safari (macOS)            ✅ Yes         Touch ID             │
│   Safari (iOS)              ✅ Yes         Face ID/Touch ID     │
│   Firefox                   ⚠️ Partial     Platform dependent   │
│   Security Keys             ⚠️ Varies      FIDO2 Level 2 req.   │
│                                                                 │
│   Fallback Strategy:                                            │
│   • Detect PRF support at registration                          │
│   • Fall back to encrypted key storage if unavailable           │
│   • Clearly communicate security implications to user           │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### MuSig2 Implementation Notes

**Key Aggregation:**

```typescript
// Simplified MuSig2 key aggregation
function aggregateKeys(pubkeys: Uint8Array[]): Uint8Array {
  // Sort pubkeys lexicographically for determinism
  const sortedKeys = [...pubkeys].sort(compareBytes);

  // Compute key aggregation coefficients
  const L = hashKeys(sortedKeys);

  // Aggregate with coefficients
  let aggregated = Point.ZERO;
  for (const pk of sortedKeys) {
    const P = Point.fromBytes(pk);
    const a = computeCoefficient(L, pk);
    aggregated = aggregated.add(P.multiply(a));
  }

  return aggregated.toBytes();
}
```

**Nonce Generation (Critical for Security):**

```typescript
// MuSig2 requires fresh, unpredictable nonces
function generateNonce(
  secretKey: Uint8Array,
  publicKey: Uint8Array,
  message: Uint8Array,
  extraRand: Uint8Array
): { secretNonce: Uint8Array; publicNonce: Uint8Array } {
  // MUST use fresh randomness for each signing session
  const rand = crypto.getRandomValues(new Uint8Array(32));

  // Derive nonce deterministically from inputs + randomness
  const k = taggedHash(
    "MuSig2/nonce",
    concat(secretKey, publicKey, message, rand, extraRand)
  );

  return {
    secretNonce: k,
    publicNonce: Point.BASE.multiply(k).toBytes()
  };
}
```

### NFC Hardware Wallet Protocol

```
┌─────────────────────────────────────────────────────────────────┐
│              NFC SIGNING PROTOCOL (APDU)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   Command                    Response                           │
│   ───────                    ────────                           │
│                                                                 │
│   SELECT APPLET              OK + Version                       │
│   ┌────────────────┐         ┌────────────────┐                │
│   │ CLA: 00        │   ──▶   │ SW: 9000       │                │
│   │ INS: A4        │         │ Version: 1.0   │                │
│   │ AID: Nuri...   │         │                │                │
│   └────────────────┘         └────────────────┘                │
│                                                                 │
│   GET PUBLIC KEY             Public Key                         │
│   ┌────────────────┐         ┌────────────────┐                │
│   │ CLA: E0        │   ──▶   │ SW: 9000       │                │
│   │ INS: 40        │         │ PubKey: 33B    │                │
│   │ Path: m/86'/...│         │                │                │
│   └────────────────┘         └────────────────┘                │
│                                                                 │
│   MUSIG2 NONCE               Nonce Commitment                   │
│   ┌────────────────┐         ┌────────────────┐                │
│   │ CLA: E0        │   ──▶   │ SW: 9000       │                │
│   │ INS: 50        │         │ R: 33B         │                │
│   │ SessionID      │         │                │                │
│   └────────────────┘         └────────────────┘                │
│                                                                 │
│   MUSIG2 SIGN                Partial Signature                  │
│   ┌────────────────┐         ┌────────────────┐                │
│   │ CLA: E0        │   ──▶   │ SW: 9000       │                │
│   │ INS: 52        │         │ s: 32B         │                │
│   │ Message hash   │         │                │                │
│   │ Agg nonce      │         │                │                │
│   │ Agg pubkey     │         │                │                │
│   └────────────────┘         └────────────────┘                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Conclusion

Nuri Wallet represents a significant advancement in Bitcoin
self-custody, combining:

1. **Stateless Security**: No persistent key storage reduces attack surface
2. **Multi-Party Signing**: MuSig2 provides privacy and efficiency
3. **Graceful Degradation**: Decaying timelocks ensure recovery is
always possible
4. **Flexible Security**: 2-of-2 and 2-of-3 configurations for different needs

The architecture ensures that users maintain full sovereignty over
their Bitcoin while benefiting from the security of multi-signature
protection and the convenience of modern authentication methods.

---

## Appendix A: Glossary

| Term | Definition |
|------|------------|
| **CSV** | CheckSequenceVerify; Bitcoin opcode for relative timelocks |
| **HSM** | Hardware Security Module; tamper-resistant key storage |
| **MuSig2** | Multi-signature scheme for Schnorr signatures |
| **PRF** | Pseudo-Random Function; WebAuthn extension for key derivation |
| **Taproot** | Bitcoin upgrade enabling Schnorr signatures and MAST |
| **UTXO** | Unspent Transaction Output; Bitcoin's accounting model |
| **WebAuthn** | Web Authentication standard for passwordless auth |

---

## Appendix B: References

1. [BIP-340: Schnorr Signatures for
secp256k1](https://github.com/bitcoin/bips/blob/master/bip-0340.mediawiki)
2. [BIP-341: Taproot](https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki)
3. [BIP-327: MuSig2](https://github.com/bitcoin/bips/blob/master/bip-0327.mediawiki)
4. [WebAuthn PRF Extension](https://w3c.github.io/webauthn/#prf-extension)
5. [Blockstream Green Security
Model](https://help.blockstream.com/hc/en-us/articles/900001391763)

---
*Post created via email from emin@nuri.com*
