+++
title = "A Passkey-Derived 2-of-2 Taproot Wallet Architecture Eliminating Seed Phrases, Mitigating Supply-Chain Risk, and Enforcing Verified, Non-Blind Signing"
date = 2025-12-02T09:50:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "a-passkey-derived-2-of-2-taproot-wallet-architecture-elimina"
+++


This post
describes a wallet architecture that removes seed phrases entirely, avoids
storing long-term private keys, and mitigates one of the largest practical
threats to software wallets today: compromise of the client application's
dependency graph or build pipeline.

The design employs two independent **passkeys**, each bound to a different
domain and each invoking the **WebAuthn PRF extension** to derive
deterministic key material. These two keys form a **2-of-2 MuSig Taproot
aggregated key**, requiring both signatures for every spend. One signing
flow occurs inside the user's application environment, and the second
occurs on a completely separate, isolated co-signing domain with
user-visible transaction decoding.

The architecture is built to address specific weaknesses in conventional
wallet designs, including seed-phrase exposure, blind signing, and
dependency-chain compromise.

---

## **1. Motivation**

### **1.1 Seed phrase exposure during import**
Seed-phrase–based wallets require the user to type or paste a BIP-39
mnemonic or private key during wallet creation or recovery. This moment is
extremely fragile:

- Mnemonics appear in plaintext in memory, visible to any malicious script
or compromised dependency.
- Clipboard use exposes secrets to OS-level observers or background
applications.
- Mobile and web environments permit DOM injection, overlay attacks,
accessibility scraping, or clipboard listeners.
- Even brief exposure is enough for silent key theft.

If the application itself (or its dependencies) is compromised, a seed
phrase can be exfiltrated the instant it touches memory. Eliminating this
step entirely removes one of the largest security liabilities in software
wallets.

### **1.2 Supply-chain compromise**
Modern front-end stacks (React, React Native, Expo, etc.) routinely
incorporate hundreds of transitive dependencies. A single dependency update
or injected build-step modification can:

- Transmit sensitive material over the network
- Alter transaction parameters
- Manipulate UI rendering of transaction data
- Log or forward key material

When a wallet relies on a single private key stored or derived within such
an environment, a supply-chain compromise allows complete and silent
draining of user funds.

### **1.3 Blind signing and misrepresentation**
In single-environment wallets, the application that constructs the
transaction is the same one that displays the transaction summary and
performs the signing. A compromised or manipulated UI can:

- Modify destination addresses
- Misrepresent amounts or fees
- Construct valid signatures over malicious transactions while showing
benign data

Without an independent verification step, the user cannot detect tampering.

---

## **2. Architectural Overview**

The system uses two passkeys:

- **Passkey A**
Registered to RPID `nuri.com` and used in the client application (web, iOS,
Android).

- **Passkey B**
Registered to RPID `confirm.nuri.com` and used exclusively on a separate
co-signing website.

Both passkeys use the **WebAuthn PRF extension**, yielding deterministic
high-entropy PRF outputs:

- `PRF_A` → used to derive signing key `k₁`
- `PRF_B` → used to derive signing key `k₂`

These keys are combined into a **MuSig 2-of-2 Taproot key**, producing a
single aggregated on-chain public key. Spending from the Taproot output
requires **both partial signatures**.

The application environment controls one signing factor.
A separate web domain controls the second.
Neither domain can access the passkey of the other due to the RPID boundary
enforced by the platform.

---

## **3. Signing Flow**

### **3.1 Transaction preparation and partial signing (`nuri.com`)**

1. The user constructs a transaction inside the application.
2. The application creates a PSBT (inputs, outputs, fees).
3. The user authenticates with **Passkey A**, generating `PRF_A`.
4. A deterministic KDF derives the key `k₁`.
5. The application creates a partial MuSig signature using `k₁`.
6. The partially signed PSBT is forwarded to the independent co-signing
domain.

The application cannot finalize the transaction. A compromised client can
only prepare a PSBT—not complete it.

---

### **3.2 Independent verification and co-signing (`confirm.nuri.com`)**

1. The user is redirected to the co-signing site.
This domain is isolated from the app by the browser and the WebAuthn RPID
model.
2. The co-signing server independently parses and decodes the PSBT.
It displays a clear, human-readable summary of the spend:
- Inputs and amounts
- Destination addresses
- Fees
- Change outputs
3. The user authenticates with **Passkey B**, producing `PRF_B`.
4. A deterministic KDF derives key `k₂`.
5. After validating the PSBT, the co-signer generates the second partial
MuSig signature.
6. `PRF_B` and `k₂` are zeroized immediately. Nothing is stored server-side.
7. The fully signed PSBT is returned to the application or broadcast to the
network.

This step provides both a second signature and an independent confirmation
of intent, mitigating blind-signing attacks.

---

## **4. Threat Analysis**

### **4.1 Seed phrase risks eliminated**
No seed phrase is ever generated, displayed, entered, or stored.
There is no clipboard exposure, no import form, no secret material in
JavaScript memory, and no attack window during wallet creation.

### **4.2 Protection against supply-chain compromise (client side)**
If the application or its dependencies are compromised:

- The malicious code cannot derive `k₂`.
- It cannot impersonate `confirm.nuri.com` or invoke Passkey B.
- It cannot finalize the signature without the co-signer’s partial
signature.
- The co-signer independently displays the true transaction details, making
tampering visible.

A client-only compromise is insufficient to steal funds.

### **4.3 Protection against co-signer compromise**
If the co-signing server or its front-end is compromised:

- The attacker cannot derive `k₁`.
- They cannot initiate a transaction because they cannot sign the first
partial.
- They cannot obtain Passkey A's PRF output due to RPID binding.

A co-signer-only compromise is also insufficient to steal funds.

### **4.4 Combined compromise requirement**
Fund theft requires coordinated compromise of:

- The application supply chain **and**
- The co-signing site supply chain
- Or a phishing attack that manipulates transaction details on **both**
sites in a consistent manner

This significantly increases the difficulty of a successful attack.

### **4.5 Blind signing mitigated**
Because transaction verification occurs at both:

- The application (initial display)
- The co-signing domain (independent decoding and display)

…the user receives two authenticated views of the same intent, closing the
common blind-signing hole that afflicts single-environment wallets.

### **4.6 No server-stored private keys**
The co-signer:

- Stores no key material
- Derives k₂ only during the WebAuthn operation
- Immediately zeroizes all sensitive data

There is no long-term key database to compromise.

### **4.7 Domain isolation via WebAuthn RPID**
The RPID binding ensures:

- The app cannot use Passkey B
- The co-signer cannot use Passkey A
- Phishing domains cannot reuse existing passkeys
- Mobile/native apps cannot trick the OS into unlocking a passkey for a
different domain

Hardware and OS enforce this isolation boundary.

---

## **5. Resulting Security Properties**

| Property | Description |
|---------|-------------|
| No seed phrases | No user-entered secrets; no import fields; no clipboard
exposure |
| Hardware-backed keys | Secrets originate in Secure Enclave / FIDO
authenticators |
| 2-of-2 MuSig | Both keys required; no unilateral spending |
| Isolation via domains | Two separate RPIDs, enforced by the platform |
| Stateless co-signer | No long-term keys; nothing to steal from the server
|
| Independent verification | Prevents blind signing; detects tampered PSBTs
|
| Supply-chain resilience | Single environment compromise is insufficient |
| Cross-platform compatibility | Works on web, iOS, Android without
extensions |

---

## **6. Conclusion**

This architecture addresses the primary attack vectors in software wallets:

- Seed phrase exposure
- Supply-chain compromise
- Blind-signing UI manipulation
- Single-key failure modes
- Server-side key theft

By distributing signing authority across two independent domains, each
backed by its own passkey and PRF output, and by requiring both signatures
for every spend, the design substantially increases the security margin
while remaining deployable in ordinary browsers and mobile apps.

It creates a practical path toward secure, cross-platform Bitcoin
self-custody without seed phrases, without extensions, and without reliance
on a trusted client software stack.

If needed, this can be expanded into a formal specification, security
analysis, or developer implementation guide.

![IMG_6836](/media/a-passkey-derived-2-of-2-taproot-wallet-architecture-elimina/IMG_6836.jpeg)

---
*Post created via email from emin@nuri.com*
