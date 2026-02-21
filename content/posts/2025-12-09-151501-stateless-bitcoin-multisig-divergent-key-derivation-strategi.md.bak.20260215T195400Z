+++
title = "Stateless Bitcoin Multisig: Divergent Key Derivation Strategies"
date = 2025-12-09T15:15:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "stateless-bitcoin-multisig-divergent-key-derivation-strategi"
markup = "markdown"
body_format = "markdown"
+++


In the implementation of non-custodial Bitcoin wallets utilizing
MuSig2 and WebAuthn (Passkeys), "statelessness" defines the
architectural constraint. The system must reconstruct key material
deterministically without relying on ephemeral state. However, the
cryptographic source of truth for the server-side co-signer presents
two distinct architectural paradigms.

This post analyzes the transition from a Client-Entropy Model to a
Hybrid-Entropy Model and the resulting determinism challenges.

## 1. Architecture A: The Client-Entropy Model (Pure PRF)

The legacy architecture prioritizes portability and zero-knowledge
properties on the server side.

**The Derivation Flow**
This model utilizes a deterministic Pseudo-Random Function (PRF)
output from the WebAuthn authenticator as the sole entropy source.
1.  **Entropy Generation:** The client performs an assertion on a
distinct "Co-signer Passkey" (domain-separated from the User Key).
2.  **Transmission:** The raw PRF bytes are transmitted to the server
over a secure channel.
3.  **Derivation:** The server acts as a pure function, mapping the
input PRF directly to a private scalar: `k_server =
Reduce(PRF_bytes)`.

**Security Properties**
* **Input Space:** Strictly client-side.
* **Server State:** None.
* **Key Independence:** Relies entirely on RPID (Relying Party ID)
separation to ensure `k_user` and `k_server` are mathematically
distinct.
* **Vector:** Use of this model implies that possession of the
specific hardware authenticator allows for the reconstruction of the
full key set without server cooperation.

## 2. Architecture B: The Hybrid-Entropy Model (Secret-Anchored)

The modern architecture shifts the root of trust to a composite
derivation scheme, introducing a server-side static secret to prevent
unilateral key reconstruction.

**The Derivation Flow**
This model treats the co-signer key as a function of both a secure
server master seed and immutable client identity metadata.
1.  **Authentication:** The client proves possession of the credential.
2.  **Composite KDF:** The server derives the private scalar using a
Key Derivation Function (KDF) that mixes a high-entropy Server Master
Secret (`S_master`) with a set of client-specific context parameters
(`C_client`) and protocol-specific constants (`P_context`).
    `k_server = HKDF(Salt=S_master, IKM=C_client || P_context)`
3.  **Context Parameters (`C_client`):** This input vector is
generalized to include immutable properties of the credential (e.g.,
public key hash, credential identifier, or attestation data), binding
the derived key strictly to a specific hardware instance.

**Security Properties**
* **Input Space:** Hybrid (Server Secret + Client Identity).
* **Server State:** Static `S_master` required.
* **Defense in Depth:** An attacker possessing the client's
authenticator cannot derive `k_server` without exfiltrating
`S_master`. Conversely, a server compromise yields no usable keys
without the client's interactive signature.

## 3. The Compatibility Challenge: Deterministic Divergence

Migrating between these architectures presents a blocking issue:
**Derivation Mismatch.**

Because `Function_A(PRF)` and `Function_B(S_master, C_client)` utilize
fundamentally disjoint input spaces, they produce orthogonal private
scalars for the same user identity.
* **Result:** The aggregated MuSig2 public key `P_agg = P_user +
P_server` changes.
* **Impact:** From the blockchain's perspective, the user's identity
(address) has rotated. The wallet derived via Architecture B is
mathematically unrelated to the wallet derived via Architecture A.

## 4. Remediation and Migration Pathways

Resolving the derivation mismatch requires selecting a canonical
"Source of Truth" for existing versus new entities.

**Strategy 1: The Protocol Adapter (Legacy Support)**
The modern server implements a conditional branch. If the request
payload matches the Legacy schema (providing raw PRF bytes), the
server bypasses the `S_master` KDF and executes the legacy reduction
function. This preserves the address space for existing users but
maintains the Architecture A security model for those specific
cohorts.

**Strategy 2: The Client Bridge (Parameter Injection)**
The client-side instantiation logic is updated to extract the
`C_client` parameters required by Architecture B even during legacy
flows. This allows the server to compute the new derivation path in
the background or migrate the user's state without changing the user
experience, effectively bridging the entropy gap.

**Strategy 3: The Hard Fork (Address Rotation)**
The system enforces Architecture B as the singular standard. Users on
Architecture A are treated as deprecated entities. A migration UX is
introduced to sign a sweeping transaction, moving UTXOs from the
`P_agg(Legacy)` address to the `P_agg(Modern)` address.

## Summary

The shift from Client-Entropy to Hybrid-Entropy represents a trade-off
between recoverability and resistance to client-side coercion. While
Architecture A offers theoretical self-sovereign recovery,
Architecture B enforces a stronger 2-of-2 security model where neither
party holds sufficient entropy to reconstruct the full keyset in
isolation.

---
*Post created via email from emin@nuri.com*
