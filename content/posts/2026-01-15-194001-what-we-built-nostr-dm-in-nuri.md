+++
title = "What We Built (Nostr DM in Nuri)"
date = 2026-01-15T19:40:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "what-we-built-nostr-dm-in-nuri"
markup = "markdown"
body_format = "markdown"
+++

![](/media/what-we-built-nostr-dm-in-nuri/cover.jpg)

What We Built (Nostr DM in Nuri)
  This is a lightweight, encrypted, relay-based 1:1 chat that lives
inside your app and uses the user’s existing wallet key material to
derive a Nostr identity. It’s wired into screens/BitcoinDebugModal.tsx
and
  exposed through components/NostrChatModal.tsx, with the support
contact hard‑coded to
npub1r7y83c4w57jc8skud7e4m6x9qt9g7s6zel6mnvj64lh00lc7tynsdx89vj.

  Identity & Key Management
  We derive a deterministic Nostr keypair from the device’s Bitcoin
private key (fallback to Ethereum key, then random if neither exists).
The Nostr private key is stored in secure storage and can be wiped on
factory
  reset.

  - Derivation: HKDF-SHA256 over sha256(btcKey) with a constant
salt/info, then validation retry loop; implemented in
lib/nostr/nostr.ts.
  - Storage: Nostr key is stored in Keychain with biometrics, via
lib/secureKeyStorage.ts (NOSTR_KEY_ID).
  - Determinism: same Bitcoin key -> same Nostr npub; factory reset
wipes local key, so a new wallet key yields a new npub.
  - The app exposes your npub suffix in the input row (tap to copy
full npub) in components/NostrChatModal.tsx.

  End‑to‑End Encryption (NIP‑17 + NIP‑44)
  We use NIP‑17 “gift wrap” with NIP‑44 v2 encryption
(XChaCha20‑Poly1305). Relays only see encrypted blobs; only the
recipient’s private key can decrypt.

  Encryption flow is implemented in lib/nostr/nostr.ts:

  - Create a “rumor” (kind 14) with the plaintext message and sender pubkey.
  - Encrypt the rumor to the recipient using a random “seal” key
(NIP‑44), sign it as kind 13.
  - Encrypt the seal to the recipient using a random “wrap” key
(NIP‑44), sign it as kind 1059 (gift wrap), tag ["p",
recipientPubkey].
  - The outer gift‑wrap (kind 1059) is published to relays; only the
recipient can decrypt it.

  NIP‑44 details (also in lib/crypto.ts):

  - ECDH shared secret is computed from secp256k1 keys.
  - We derive the NIP‑44 key as HKDF(SHA256(x-only-shared-secret),
info="nip44-v2").
  - Payload encryption is XChaCha20‑Poly1305 with a 24‑byte random nonce.

  Important security note
  Right now the sender’s long‑term secret is not used to sign the
rumor. That means the content is confidential (E2E), but sender
identity is not cryptographically authenticated — any sender could
spoof the pubkey
  inside the rumor. If you want authenticated sender identity, we
should sign the rumor (or switch to a NIP‑44 DM flow that includes
authentication). This is the one notable integrity gap today in
lib/nostr/nostr.ts.

  Send Path (Client -> Relay)
  Handled in components/NostrChatModal.tsx.

  - Validate recipient pubkey; block self‑chat.
  - Create gift wrap with createNip17GiftWrap, then send ["EVENT",
giftwrap] over all open relay WebSockets.
  - Log: sender, recipient, event id, message length, and relay
acknowledgements.
  - UI immediately appends the outgoing message to local state.

  Receive Path (Relay -> Client)
  Also in components/NostrChatModal.tsx.

  - Subscribe to kind 1059 with a #p tag equal to our pubkey.
  - Deduplicate by event id and decrypt via openNip17GiftWrap.
  - Extract rumor content + sender pubkey, then display as an incoming message.
  - Auto‑add sender to local contacts.

  Catch‑Up Behavior (Missed Messages)
  We added a light “catch‑up” flow that pulls missed messages after reconnect.

  - We store a last_seen timestamp per pubkey in Keychain using
NOSTR_LAST_SEEN_CACHE_KEY in lib/nostr/storage.ts.
  - On each relay subscription, we add since = last_seen - 60s to the
filter to backfill recent messages.
  - This is implemented in components/NostrChatModal.tsx, and the
cache is wiped on factory reset in services/factoryReset.ts.

  Relay Connectivity
  We use a small set of public relays by default (no infra needed right now).

  - Default relays: wss://relay.damus.io, wss://relay.primal.net,
wss://nostr21.com.
  - WebSocket connections are created while the chat modal is open and
closed when it closes.
  - If the app is closed/offline, real‑time delivery pauses; catch‑up
works if the relays still have the message.

  Chat UX + Contact List
  The UI is minimal and built to fit the app’s design language.

  - Chat list shows: Private Support, Group Support (disabled), and
dynamic contacts; last message + date/time appear in subtitle.
  - Active chat title is last 5 chars of recipient npub, with a copy icon.
  - Back link is text (“< back”) and underlined for clarity.
  - Composer is one‑line input with a send icon inside; send can also
use keyboard “Send”.
  - “You” label removed; only your own suffix is shown and tappable to copy.

  All of this lives in components/NostrChatModal.tsx.

  Support Logic
  Support is hard‑coded and shown to all non‑support users.

  - Support npub configured in screens/BitcoinDebugModal.tsx.
  - If the user’s npub matches support, the support chat is hidden and
self‑chat is blocked.

  Storage & Reset
  We persist only what we need.

  - Contacts cache: @cache:nostr_contacts in Keychain.
  - Last‑seen cache: @cache:nostr_last_seen in Keychain.
  - Messages are in memory only; they do not persist across modal
closes or app restarts.
  - Factory reset clears all of the above + Nostr private key (see
services/factoryReset.ts).

  What “End‑to‑End Encrypted” Means Here

  - Confidentiality: Relays never see plaintext; only the recipient
with the private key can decrypt.
  - Forward secrecy: Each message uses fresh seal/wrap keys.
  - Authentication: Not yet guaranteed — sender identity can be
spoofed because the rumor isn’t signed.

  Operational Notes

  - No infra required today. If you want stronger reliability, run
your own relay and add it to the list.
  - No push notifications; catch‑up works when the chat opens.
  - Delivery depends on relay retention; some relays drop DMs.

  If you want me to add sender authentication (signed rumor) or
background delivery, I can outline the minimal changes.

---
*Post created via email from emin@nuri.com*
