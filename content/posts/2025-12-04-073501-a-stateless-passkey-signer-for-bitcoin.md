+++
title = "A Stateless Passkey Signer for Bitcoin"
date = 2025-12-04T07:35:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "a-stateless-passkey-signer-for-bitcoin"
+++


Stateless Bitcoin Wallet With Passkeys and a Minimal Signer


I’m working on a Bitcoin wallet that is fully stateless.


By stateless I mean: the Bitcoin private key is never stored anywhere. Not
on the phone, not on a server, not in a database. It is derived
deterministically from a passkey PRF (WebAuthn / FIDO2) whenever it’s
needed, used inside a very small signing environment, and then thrown away
again.


In this post I want to describe the architecture I’m building, how I’m
thinking about “no blind signing”, and where I still see open security
questions. I’d love feedback, especially from people who build wallets,
HSMs, or work with WebAuthn and Bitcoin PSBTs.

------------------------------

Using Passkeys as the Root of a Wallet


The basic idea:


   -

   Each user has a passkey (WebAuthn / FIDO2 credential) with the PRF
   extension enabled.
   -

   I call the output of that extension the passkey PRF.
   -

   That PRF output is a high-entropy secret that never leaves the
   authenticator in raw form; it’s exposed only through the PRF interface.
   -

   I deterministically derive a Bitcoin private key from that PRF output.
   The PRF is effectively my seed.


So every time the user approves a WebAuthn request (Face ID, fingerprint,
PIN, whatever the device uses), the signer can re-derive the same Bitcoin
key without ever having to store it.


This effectively turns a regular passkey into the seed phrase of a
single-sig Bitcoin wallet, but:


   -

   there is no mnemonic,
   -

   nothing written down,
   -

   and no file to back up.


The security of the wallet becomes the security of the passkey (plus how I
handle the signing environment, of course).

------------------------------

Inspirations: FileKey, Bitwarden, and 1Password


This idea didn’t come out of nowhere. It’s inspired by a few projects that
already use passkeys as high-entropy secrets:


   -

   FileKey.app <https://filekey.app/>[image: Attachment.png] – Stateless
   file encryption and decryption. It uses the passkey PRF as input, derives
   keys on demand, and never stores them permanently.
   -

   Bitwarden <https://bitwarden.com/>[image: Attachment.png] and 1Password
   <https://1password.com/>[image: Attachment.png] – Both support unlocking
   your password manager with passkeys. The passkey PRF (or equivalent
   credential secret) is used to unlock and protect your vault, including in
   web environments.


What I’m trying to do is bring this same pattern to Bitcoin: use passkeys
as the root secret for a stateless signing setup.

------------------------------

Tech Stack: Expo / React Native, Everywhere


I’m building the app with Expo React Native. The reason is simple: I want
the stateless signer to run in as many environments as possible:


   -

   Android
   -

   iOS
   -

   Web / browser


The “wallet” part of the app is just a front end:


   -

   It prepares transactions.
   -

   It displays balances and history.
   -

   It never holds a private key.


All the actual signing happens in a separate, tightly controlled
environment.

------------------------------

Two Environments: Preparer vs. Signer


A key design decision is to separate:


   1.

   Where transactions are prepared, and
   2.

   Where transactions are signed.


1. Transaction preparation


This is the regular wallet interface:


   -

   It lets you pick UTXOs, set outputs, choose fees, and review everything.
   -

   It creates a PSBT (Partially Signed Bitcoin Transaction – BIP-174,
   BIP-370) instead of a raw transaction.
   -

   That PSBT is then passed to the signer.


This can live on the phone, in the browser, or any environment. It’s
stateless and doesn’t need the private key.


2. Minimalistic signing website


Signing happens on a separate website (or web app) whose only job is to:


   -

   Take a PSBT,
   -

   Derive the Bitcoin key from the passkey PRF,
   -

   Sign the PSBT, and
   -

   Return the signed transaction / PSBT (for example as text and as a QR
   code).


The important properties of this signer:


   -

   It is extremely minimalistic.
   -

   It can be self-hosted.
   -

   It’s designed to be easy to audit (tiny codebase, very few dependencies).


From there:


   -

   The signed transaction can be sent back to the wallet, or
   -

   Any wallet can scan the QR code and broadcast it, or
   -

   The user can copy the hex and broadcast it via their node / another
   service.


The idea is: the signer is a small, highly controlled enclave. The app on
the phone is “just UI”.

------------------------------

How I Try to Avoid Blind Signing


One of my goals is that this system does not turn into a blind-signing
nightmare.


What I can guarantee in the signer


I can design the signer so that it:


   -

   Only signs structured Bitcoin PSBTs (BIP-174 / BIP-370), never arbitrary
   bytes.
   -

   Parses and validates the PSBT and refuses to sign anything it doesn’t
   fully understand.
   -

   Always shows the decoded transaction to the user, including:

   -

      Inputs
      -

      Outputs
      -

      Fees
      -

      Timelocks
      -

      Scripts / conditions (e.g., CSV)



…and it requires explicit user confirmation on that screen.


If I do that, there is no “blind-signing API”. There’s simply no way to
silently sign random data; everything must be a valid PSBT that the signer
can decode and display.


What I cannot cryptographically guarantee


Even with all that, there are still things this architecture cannot
magically solve:


   -

   I still rely on the signer UI being honest.

   -

      If the signer website is compromised, serving malicious JavaScript,
      or hit by a supply-chain attack, it could lie about what it shows.

   -

   I still rely on the user actually reading what they are about to sign.

   -

      If they just click “approve” without looking, no architecture can fix
      that.

   -

   I still rely on the PSBT decoder and display logic being correct.

   -

      Bugs in the parser could hide weird scripts or fields and create
      misleading displays.



So I can eliminate a blind-signing API, but I can’t cryptographically force
the UI to be honest or the user to pay attention. That’s just reality.

------------------------------

Optional Co-Signing Server + CSV Exit


On top of the single-sig stateless setup, I’ve also experimented with
adding a co-signing server and a CSV escape hatch.


Rough idea:


   -

   Use a 2-of-2 script:

   -

      One key is derived from the user’s passkey PRF (stateless, as
      described above).
      -

      The second key is on a co-signing server.

   -

   Add a CSV (CheckSequenceVerify) condition:

   -

      After, say, 10,000 blocks (~3 months), the coins can be spent with
      only the user’s key.



What this buys you:


   -

   If a single key leaks, it doesn’t automatically mean the wallet can be
   drained instantly.
   -

   If the co-signing server disappears, gets shut down, or you just don’t
   trust it anymore, you still have an exit:

   -

      Wait out the CSV period, then spend with your single key.



The user doesn’t know or control the second key, but they also don’t need
it forever. The CSV exit guarantees that in the worst case, after a delay,
the funds are fully under their control again.


This is not perfect security, but it’s a nice trade-off:


   -

   Extra friction for an attacker,
   -

   No catastrophic loss if the co-signer goes away.

------------------------------

Putting It All Together


So the full picture looks like this:


   -

   Key derivation

   -

      Passkey PRF → deterministic Bitcoin private key → never stored.

   -

   Wallet front end (Expo / React Native)

   -

      Runs on Android, iOS, and web.
      -

      Prepares PSBTs, shows balances, etc.
      -

      Completely stateless: no private keys, only public data + PSBTs.

   -

   Minimal signer

   -

      Small web app (self-hostable).
      -

      Uses WebAuthn passkey to derive the key and sign PSBTs.
      -

      Only signs structured PSBTs, always shows humans a decoded view, no
      arbitrary-data signing.

   -

   Optional 2-of-2 + CSV

   -

      Co-signing server adds another hurdle for attackers.
      -

      CSV exit (~10,000 blocks) ensures you can always eventually move
      funds with just your passkey-derived key.


------------------------------

Open Questions and Call for Feedback


I’m pretty happy with the high-level concept, but I’m sure there are blind
spots and attacks I haven’t thought about yet.


Things I’m especially interested in feedback on:


   -

   Subtle issues around the passkey PRF and derivation (WebAuthn details,
   browser quirks, platform differences).
   -

   Attack vectors in moving PSBTs between the “preparer” and the “signer”
   (QR codes, deep links, copy-paste, etc.).
   -

   Better ways to design the co-signer + CSV setup (e.g. script templates,
   edge cases).
   -

   Threat models I’m underestimating (phishing, UI spoofing, compromised
   devices, etc.).


If you see mistakes, risks, or better patterns, please challenge this
architecture.

The goal is not just to build something clever, but something that actually
holds up in the real world.

Short answer:

Yes, what you’re describing is absolutely feasible in principle, and it can
be built to avoid classic “blind signing”… but there are a bunch of subtle
pitfalls in:


   -

   how you use the passkey PRF,
   -

   how you move the PSBT between “preparer” and “signer”, and
   -

   how you design co-signing + CSV exit scripts.


I’ll walk through the architecture and the main traps, then finish with a
big list of security questions you can use as a design checklist.

------------------------------

1. Let me restate your architecture in more formal terms


Just to align:


   1.

   Key material

   -

      Each user has a passkey (WebAuthn / FIDO2 credential) with the PRF
      extension enabled.
      -

      When the signer runs, it asks the authenticator for a 32‑byte PRF
      output bound to that credential.
      -

      You treat this PRF output as a seed (or IKM) to deterministically
      derive a Bitcoin private key / root.

   2.

   Statelessness

   -

      The wallet UI (Expo app / browser / whatever) never stores private
      keys.
      -

      The signer (a minimal website, self‑hostable, maybe also packaged as
      a PWA) derives the private key on the fly from the passkey PRF,
signs, then
      discards it from memory.

   3.

   Flow

   -

      Environment A (wallet front‑end) builds a PSBT (or unsigned tx) using
      UTXOs, outputs, fees, etc.
      -

      That PSBT is encoded as QR (or other channel) and passed to
      Environment B (the signer website).
      -

      Signer website:

      -

         Decodes PSBT.
         -

         Displays transaction details in a minimal, auditable UI.
         -

         Uses passkey PRF → Bitcoin key → signs.
         -

         Returns the signature / signed PSBT as QR or message.

      -

      Broadcasting happens elsewhere (wallet, other node, or third party).

   4.

   Optional co‑signer

   -

      Outputs are encumbered with a script like:

      IF 2-of-2 (user key + co-signer key) ELSE CSV(10,000 blocks) + single
      user key ENDIF, using OP_CHECKSEQUENCEVERIFY.
      -

      So normally you need user key + co-sign server. If co-sign server
      disappears, user alone can spend after ~10k blocks (~70 days).



That’s how I read you. If that matches, everything below applies directly.

------------------------------

2. Is this concept feasible?


Yes.


All of these pieces exist today:


   -

   PRF-capable passkeys that return a 32‑byte secret on demand.
   -

   Real systems using passkey PRF for encryption and stateless key
   derivation (Bitwarden for vault encryption, FileKey for file encryption,
   and others).
   -

   Stateless signing frontends that just take PSBTs, sign in-memory, and
   output the result.


You are basically doing: “FileKey, but instead of encrypting files, it
signs Bitcoin PSBTs.” That’s very reasonable.


Main feasibility caveats:


   -

   Platform support: PRF is still rolling out. It works in many
   Chromium-based browsers, not always on Safari / all authenticators yet, and
   mobile support can be spotty.
   -

   Expo RN: you’ll need bridges to native WebAuthn/FIDO2 APIs (with PRF) on
   Android/iOS. That’s more engineering, not a fundamental blocker.


From a cryptographic / Bitcoin perspective: yes, you can do exactly what
you’re proposing.

------------------------------

3. Does this eliminate blind signing?


What you can guarantee


You can design the signer so that:


   -

   It only signs structured Bitcoin PSBTs (BIP‑174/370), not arbitrary
   bytes.
   -

   It parses the PSBT and refuses to sign anything it doesn’t fully
   understand.
   -

   It always shows the decoded transaction (inputs, outputs, fee,
   timelocks, scripts) and requires explicit user confirmation.


If you do that, you have no blind-signing API. There is simply no way to
“silently” sign arbitrary stuff—everything must be a valid PSBT the signer
can decode & display.


What you cannot cryptographically guarantee


You still rely on:


   -

   The signer UI being honest (no UI corruption / XSS / supply-chain
   attack),
   -

   The user actually reading what they sign,
   -

   The PSBT decoder being correct (no parser bugs that hide weird scripts /
   fields).


So you can say:


“This wallet does not support blind signing as a feature: it only signs
PSBTs whose semantics are fully parsed and shown to the user.”


…but you cannot guarantee that “no user ever signs something they don’t
truly understand”. That’s ultimately a UX and education problem, not a
cryptographic one.

------------------------------

4. How to safely use the passkey PRF for Bitcoin keys


Very important detail: the WebAuthn PRF output should be treated as Input
Keying Material (IKM), then fed into a proper KDF (HKDF) to derive
purpose-bound keys. This is explicitly recommended by people implementing
PRF for encryption.


Suggested derivation scheme


   1.

   PRF output (IKM)

   -

      During authentication with your RP ID (e.g. wallet.yourdomain.com),
      request PRF with a salt like "bitcoin-wallet-root".

   You get:

   prf_ikm (32 bytes, per-credential, secret).
   2.

   Run HKDF on it

master_key_material = HKDF(
    ikm = prf_ikm,
    salt = "btc-mainnet" or "btc-testnet" etc,
    info = "stateless-btc-wallet v1",
    L = 64 bytes
)


   2.

   Split into:

root_priv_key = master_key_material[0:32]
root_chain_code = master_key_material[32:64]


   2.

   Now you have something that looks like a BIP32 root (privkey + chain
   code).
   3.

   Apply standard HD derivation (BIP32/BIP84/etc)

   -

      Use your standard derivation path, e.g. m/84'/0'/0'/0/i for native
      segwit, or a custom descriptor.



This gives you:


   -

   Domain separation between:

   -

      Bitcoin vs other uses,
      -

      Mainnet vs testnet,
      -

      Potential future versions.

   -

   A surface that is very similar to normal HD wallets—so you can reuse a
   lot of wallet logic and tooling.


Privacy & multi-address requirement


Please, don’t make it a single static private key:


   -

   For privacy and basic good practice, you really need many addresses.
   -

   The stateless signer can recompute the same xprv/xpub from PRF each
   time, then derive keys on demand.
   -

   The watching-only side (your backend or the client) can hold just the
   xpub/descriptor, which is harmless if leaked.


Questions you should answer here (see also the big list later):


   -

   Do you want multiple accounts from the same PRF (e.g. “savings”,
   “spending”)? If yes, how do you encode that into HKDF inputs?
   -

   How do you encode network (mainnet/testnet) so users never cross-fund?

------------------------------

5. The split: “preparer” vs “signer” and the no‑blind‑signing goal


PSBT path and attack surface


Threat: The PSBT is built by the “preparer” wallet UI, which could be
compromised.


Mitigations on the signer:


   1.

   Strict PSBT policy

   -

      Only support a small set of script templates:

      -

         Simple P2WPKH / P2TR,
         -

         Your exact 2-of-2-with-CSV template,
         -

         Maybe a known change-output descriptor.

      -

      Reject everything else:

      -

         Unknown script types,
         -

         Exotic sighash flags,
         -

         Non-standard annexes, proprietary fields, etc.

      2.

   Full-field display

   -

      For each output:

      -

         Destination address (and decode script type),
         -

         Amount in BTC + fiat equivalent (if you can fetch rates),
         -

         Whether it is recognized as “change back to your wallet” (via
         descriptor matching).

      -

      Global:

      -

         Total input sum, total output sum, fee amount, fee rate (sat/vB).
         -

         Locktime, any sequences that imply RBF or CSV constraints.

      -

      For your CSV structure:

      -

         Clearly state “These coins are locked under a 2-of-2 script with
         fallback to single-key spend after ~X days”.

      3.

   Sane defaults and warnings

   -

      Warnings for:

      -

         Fees above some threshold,
         -

         Sending all funds out of the wallet,
         -

         Scripts that change the security model (e.g. sending to non‑CSV
         addresses when wallet usually uses CSV).



If you keep the signer’s codebase very small and auditable, and you never
add an API to “sign arbitrary bytes”, you’ve done almost everything you
reasonably can against blind signing.


Channel between preparer and signer (QR, etc.)


   -

   QR / UR2 works fine but remember PSBTs can get large → use animated UR
   or similar scheme.
   -

   The signer should verify:

   -

      Network matches (mainnet vs testnet),
      -

      Inputs belong to the expected descriptor (if possible),
      -

      There are no weird unknown fields.



If someone compromises the preparer, they can still build a malicious
PSBT—but they can’t make you blind-sign it; the signer will show what
you’re actually doing.

------------------------------

6. Co-signing server + CSV exit


You’re basically building a timelocked 2-of-2 scheme:

OP_IF
    2 <user_pub> <server_pub> 2 CHECKMULTISIG
OP_ELSE
    <10000> CHECKSEQUENCEVERIFY DROP
    <user_pub> CHECKSIG
OP_ENDIF

Roughly that.


What this buys you


   -

   If user key leaks but co-signer is safe:

   -

      Attacker can’t spend immediately—needs co-signer cooperation.
      -

      Or can only spend via the CSV path after 10000-block confirmations of
      the funding UTXOs.

   -

   If co-signer key leaks but user key is safe:

   -

      Attacker still can’t do anything; they need the user’s PRF-derived
      key.

   -

   If co-signer disappears:

   -

      User waits ~10k blocks and then spends alone via CSV.



So yes: one key exposure does not immediately drain the wallet, assuming
the scripts are correct and you never create UTXOs with weaker scripts.


Things to be careful about


   1.

   Script uniformity

   -

      Your wallet must always use the same protective script for all UTXOs
      in that wallet.
      -

      No “oops this one address was plain P2WPKH”; that’s how funds get
      drained if a key leaks.

   2.

   Timelock length

   -

      10,000 blocks ≈ 10,000 / 144 ≈ 69.4 days.
      -

      That’s a long time to be stuck if the co-signer disappears and you
      want funds now.
      -

      Consider whether 7–30 days would be a better UX/security tradeoff.

   3.

   Co-signer policy

   -

      Co-signer can enforce spending policies:

      -

         Check the PSBT for suspicious destinations / amounts,
         -

         Enforce per-day limits, whitelists, etc.

      -

      But if your signer is already safe and non-blind, the co-signer
      mainly mitigates key compromise, not UI compromise.

   4.

   Implementation complexity

   -

      You’re now relying on:

      -

         Correct script assembly for P2WSH / P2TR scripts,
         -

         Correct handling of nSequence and CSV semantics,
         -

         Wallet logic that never accidentally uses the wrong branch.



You absolutely can make this work, but test the hell out of CSV and
script-path choice.

------------------------------

7. Platform / implementation thoughts (Expo, web, self-hosting)


   -

   Sign­er as a static site

   -

      Make it a single-page app with:

      -

         No backend,
         -

         Built artifact pinned by a content hash.

      -

      Users can:

      -

         Host it themselves (e.g. GitHub Pages / static hosting),
         -

         Or even download a single index.html and run fully offline.

      -

   Reproducible builds

   -

      Publish the source + instructions so people can build it and verify
      hashes.
      -

      This is key for “minimal, auditable signer” credibility.

   -

   RP ID strategy for passkeys

   -

      Use one canonical RP ID (e.g. signer.yourdomain.com) for:

      -

         Web signer,
         -

         Native apps (via associated domains).

      -

      This way, the same passkey works across web + mobile and the PRF
      output is consistent.

   -

   PRF availability

   -

      Be prepared to:

      -

         Detect when PRF isn’t supported and fail closed (no fallback to
         weak crypto),
         -

         Or have a separate non‑passkey-based wallet mode.


------------------------------

8. Security questions to challenge your design


You asked for a lot of questions, so here’s a structured list you can work
through. You don’t need to answer them to me; they’re for your design docs
and threat model.


A. Passkey / PRF usage


   1.

   Domain separation

   -

      Exactly what goes into:

      -

         PRF salt(s)?
         -

         HKDF salt and info?

      -

      How do you separate:

      -

         mainnet vs testnet vs regtest,
         -

         app v1 vs v2,
         -

         Bitcoin vs any future chain you might support?

      2.

   Key rotation

   -

      If the passkey is compromised / revoked:

      -

         How does the user migrate to a new PRF-derived root?
         -

         Do you have a built-in “rotate wallet” flow that sweeps funds from
         old script to new script?

      3.

   Passkey lifecycle

   -

      What happens if:

      -

         User loses all devices with that passkey?
         -

         Cloud-synced passkeys leak (e.g., Apple/Google compromise
         scenario)?

      -

      Is “co-signer + CSV” your only mitigation?

   4.

   PRF availability & fallback

   -

      If PRF is not supported in a browser / platform, do you:

      -

         Fail hard (“this wallet requires PRF”)?
         -

         Or silently degrade? (I’d strongly suggest fail hard.)


------------------------------

B. Transaction preparation (wallet UI)


   1.

   Descriptor correctness

   -

      Where do descriptors live?

      -

         On server? In client local storage?

      -

      How do you ensure they always match what the signer actually derives
      from the PRF?

   2.

   UTXO discovery

   -

      How do you learn which UTXOs belong to the wallet?

      -

         Own node?
         -

         Public APIs?

      -

      Threat: malicious backend “hides” UTXOs so user thinks they have less
      than they do.

   3.

   Change detection

   -

      How do you mark an output as “change” so the signer can show “this
      stays in your wallet”?
      -

      Do you enforce that change always returns to the same script type
      (e.g. CSV-protected script)?


------------------------------

C. Signer website / app


   1.

   PSBT strictness

   -

      Which PSBT versions and fields are allowed?
      -

      Do you reject:

      -

         Unknown key types?
         -

         Partial signatures?
         -

         Non-standard script types?

      2.

   Display completeness

   -

      Are you showing:

      -

         All outputs, including those with tiny amounts (dust)?
         -

         All scripts (including weird taproot paths)?
         -

         Locktime and nSequence for each input?

      3.

   No “sign arbitrary bytes” feature

   -

      Can any API path produce a signature without going through the PSBT
      decode + display flow?

   4.

   Supply chain integrity

   -

      How do you prevent:

      -

         Malicious updates getting pushed to users?
         -

         XSS / dependency hijack from injecting code that hides outputs?


------------------------------

D. Co-signing server


   1.

   Key storage

   -

      Is the co-signer key in HSM?
      -

      Can you rotate it without breaking the CSV unlock path?

   2.

   Policy engine

   -

      Does the server:

      -

         Parse and enforce policies on PSBTs (whitelist, limits), or
         -

         Just blindly sign whatever is sent?

      3.

   Availability / DoS

   -

      What happens if the co-signer is unavailable for hours/days?
      -

      Is there a clear UX showing “you now have to wait N blocks to use CSV
      path”?


------------------------------

E. Recovery, UX, and “oh shit” scenarios


   1.

   User education

   -

      How do you explain:

      -

         Statlessness,
         -

         CSV delay exits,
         -

         Need to rotate passkeys if device is compromised?

      2.

   Incident response

   -

      If you detect your signer site or co-signer infra was compromised:

      -

         How do you notify users?
         -

         Is there a “mass move everything to a new descriptor” plan?

      3.

   Monitoring

   -

      Are you watching the chain for:

      -

         Spending through CSV path (which might signal server downtime),
         -

         Suspicious spends that don’t match the expected origin (e.g., user
         denies making them)?


------------------------------

9. Bottom line


   -

   Yes, the concept is feasible.
   -

   Yes, you can design the signer so there’s effectively no blind-signing
   feature—only parsed, displayed PSBTs are ever signed.
   -

   No, you can’t mathematically guarantee users will always fully
   understand what they sign—but your separation of “preparer” and “minimal
   signer” is a strong, clean architecture to minimize that risk.
   -

   The co-signing + CSV setup is a solid way to ensure a single key leak
   doesn’t immediately nuke the wallet, provided:

   -

      Every UTXO uses the correct script template,
      -

      You’ve tuned CSV delays to a reasonable time window.



If you like, next step we can zoom into one slice (e.g., exact HKDF /
derivation scheme, or the CSV script & descriptors) and I can help you nail
down something you’d be comfortable publishing as a spec.

![IMG_6888](/media/a-stateless-passkey-signer-for-bitcoin/IMG_6888.png)

![IMG_6901](/media/a-stateless-passkey-signer-for-bitcoin/IMG_6901.png)

![IMG_6889](/media/a-stateless-passkey-signer-for-bitcoin/IMG_6889.png)

---
*Post created via email from emin@nuri.com*
