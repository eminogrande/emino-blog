+++
title = "Spark Wallet UX + Lightning Flow — Chronological Build Log"
date = 2026-01-09T14:25:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "spark-wallet-ux-lightning-flow-chronological-build-log"
markup = "markdown"
body_format = "markdown"
+++

![](/media/spark-wallet-ux-lightning-flow-chronological-build-log/cover.jpg)

# Spark Wallet UX + Lightning Flow — Chronological Build Log

  ## Briefing and Constraints

  You asked for the Spark wallet to look exactly like the existing
Bitcoin screen, keep code minimal, and avoid duplicate/legacy code.
You also set strict process rules: no git commands, no tests,
approvals before implementation, and short, precise responses. You
wanted the receive/send flow to mirror Bitcoin UI and to support
Lightning invoices, LNURL, and
  later onchain withdrawals from Spark.

  ## Phase 1 — UI Parity and Automatic Claiming

  1. Goal: Make screens/SparkBitcoinWalletScreen.tsx visually match
screens/BitcoinScreen.tsx.
  2. Key changes: Spark screen styling, spacing, typography, and
button layout aligned to the Bitcoin screen; receive and send buttons
matched exactly.
  3. Behavior change: Spark screen now auto-checks for pending
transfers and auto-claims them into the Spark wallet.
  4. Apple Pay: The Apple Pay header button stayed, with a placeholder
for passing the Spark deposit address later.

  ## Phase 2 — Receive Modal Redesign (Spark)

  1. Goal: Make Spark receive screen match Bitcoin receive screen layout.
  2. Key changes in screens/SparkBitcoinReceiveModal.tsx:
      1. Address at the top.
      2. QR code positioned in the same layout as Bitcoin receive.
      3. Share / tap-to-copy interactions aligned with Bitcoin UI.
  3. Invoice creation UX:
      1. A sats input field styled like the Bitcoin send amount input.
      2. Euro line under it for parity.
      3. The button changed to “Create Invoice”.
  4. Behavior:
      1. Before invoice creation: show deposit address; hide invoice QR.
      2. After invoice creation: show only invoice + invoice QR in the
same style.

  ## Phase 3 — Caching and Responsiveness

  1. Goal: Remove long loading delays.
  2. Changes:
      1. Cached Spark deposit address and balance.
      2. Spark screen loads from cache first and refreshes in background.

  ## Phase 4 — Spark Send Flow and Confirmation

  1. Goal: Mirror Bitcoin send flow with a final confirmation step.
  2. Changes:
      1. Scan or paste moves into screens/SparkLightningSendModal.tsx.
      2. Sender sees a confirm screen before any payment is sent.
      3. Zero-amount invoices prompt for amount entry instead of sending.

  ## Phase 5 — LNURL and Lightning Address Support

  1. Goal: Support LNURL pay and Lightning address inputs.
  2. New service: services/SparkLnurlService.ts added:
      1. Normalize inputs (strip lightning: prefix).
      2. Resolve LNURL pay request (resolveLnurlPayRequest).
      3. Request invoice from LNURL callback (requestLnurlInvoice).
  3. Send modal changes in screens/SparkLightningSendModal.tsx:
      1. Accept LNURL bech32, LNURL URL, and Lightning address.
      2. Clamp amount to LNURL min; auto-fill minimum.
      3. Hide network errors from user UI; keep them for logs.
      4. If invalid input, clear prefill and highlight request input
instead of showing invalid data.

  ## Phase 6 — Onchain Withdrawals from Spark

  1. Goal: Allow “normal Bitcoin address” sends (Spark → L1).
  2. Service update in services/SparkBitcoinWalletService.ts:
      1. withdrawToBitcoinAddress uses Spark getWithdrawalFeeQuote + withdraw.
      2. Default exit speed: ExitSpeed.MEDIUM.
      3. Logs truncate address for safety.
  3. Screen logic update in screens/SparkBitcoinWalletScreen.tsx:
      1. Detect onchain address in handleConfirmSend.
      2. Route to withdrawToBitcoinAddress instead of payLightningInvoice.
      3. Refresh Spark balance and pending deposits after withdraw.

  ## Phase 7 — UX Refinements You Requested

  1. Invalid prefill behavior:
      1. If paste/scan is not valid invoice/address/LNURL, the input
is cleared and highlighted.
  2. Input focus and keypad:
      1. After valid prefill, amount input auto-focuses.
      2. Cursor stays at the end of the amount.
      3. Number pad opens immediately.
  3. Centering:
      1. Amount block is vertically centered between header and CTA.
  4. Title logic:
      1. Header shows memo if present.
      2. Otherwise “Send Lightning” or “Send Bitcoin” (onchain).

  ## How You Guided the Build

  1. You gave clear visual comparisons (Bitcoin screen as the exact target).
  2. You caught UI mismatches quickly (icon, padding, layout) and
asked for 1:1 copy.
  3. You prioritized minimal code and “no fallback” logic.
  4. You approved changes step-by-step and clarified edge cases:
      1. Zero-amount invoices should prompt.
      2. LNURL should be pay-only for now.
      3. Network errors should not be user-facing.
  5. You pushed for exact UX flow consistency, especially around
confirmation, validation, and amount entry.

  ## What We Did Not Do

  1. No git commands.
  2. No tests (explicitly requested).
  3. No changes to the original Bitcoin screen.

  ## Current State Summary

  1. Spark wallet UI matches Bitcoin screen layout.
  2. Receive modal matches Bitcoin receive flow, with Spark deposit
address and invoice creation.
  3. Send modal supports Lightning invoices, LNURL, Lightning
addresses, and onchain BTC addresses.
  4. Invalid input never pre-fills; amount flow is focused and centered.
  5. Spark balance and deposit address are cached for faster UI.

---
*Post created via email from emin@nuri.com*
