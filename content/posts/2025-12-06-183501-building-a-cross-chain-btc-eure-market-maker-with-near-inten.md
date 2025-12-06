+++
title = "Building a Cross‑Chain BTC ↔ EURe Market Maker with NEAR Intents & 1‑Click"
date = 2025-12-06T18:35:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "building-a-cross-chain-btc-eure-market-maker-with-near-inten"
+++


Over the last days we wired up a complete BTC ↔ EURe swap stack:

  - A mobile‑first swap UI at emino.app/intent/.
  - An advanced tester & history view at emino.app/intent/intend/.
  - A live solver monitor at emino.app/solver/.
  - A real AMM solver that provides liquidity between BTC (on Bitcoin
mainnet) and EURe (on Gnosis) via
    NEAR Intents + Defuse 1‑Click.

  This post documents how it all fits together, how swaps flow through
the system, where the 0.3% “margin”
  comes from, and how a solver operator can deposit, monitor, and
eventually withdraw profits.

  ———

  ## 1. High‑Level Overview

  At a high level we have four pieces:

  1. User UI (emino.app)
      - /intent/ – simple mobile‑first page to start a BTC ↔ EURe swap.
      - /intent/intend/ – advanced JSON tester + history of swaps
started through this server.
  2. UI Server (port 4100)
      - Express server that:
          - Serves the static HTML/JS for /intent/ and /intent/intend/.
          - Exposes a small API:
              - POST /api/intend/btc-to-eure
              - POST /api/intend/eure-to-btc
              - GET /api/intend/history
              - GET /api/intend/status/:depositAddress
          - Talks to the Defuse 1‑Click API
(https://1click.chaindefuser.com) for quotes and status.
  3. NEAR Intents + Solver Relay
      - NEAR Intents contract (intents.near) holds token reserves and
tracks intents.
      - Solver Relay (wss://solver-relay-v2.chaindefuser.com/ws)
forwards quote requests from 1‑Click to
        solvers and receives their responses.
  4. Our AMM Solver
      - Runs the official near-intents-amm-solver code with:
          - AMM_TOKEN1_ID =
nep141:gnosis-0x420ca0f9b9b604ce0fd9c18ef134c705e5fa3430.omft.near
(EURe on
            Gnosis).
          - AMM_TOKEN2_ID = nep141:btc.omft.near (BTC on NEAR).
      - Maintains a constant‑product AMM over the EURe/BTC reserves on
the Intents contract.
      - Listens to quote requests via WebSocket, calculates prices
with a margin, signs NEP‑413 quotes,
        and updates its view of reserves after intents execute.

  The UI and the solver are decoupled. The UI talks only to 1‑Click;
the solver talks only to the solver
  relay + NEAR. The relay + 1‑Click route quotes and intents between them.

  ———

  ## 2. The User Experience: /intent/ and /intent/intend/

  ### /intent/: Mobile‑First Swap UI

  This is meant to be the “one‑screen” test UI:

  - Two tabs:
      - BTC → EURe
      - EURe → BTC
  - Fields:

    For BTC → EURe:
      - Amount you send (satoshis) – BTC in sats.
      - EURe receiver (Gnosis EVM) – EVM address on Gnosis.
      - BTC refund address – Bitcoin bech32 address.

    For EURe → BTC:
      - Amount you send (EURe) – EURe amount, decimal.
      - BTC receiver address – BTC address to receive the swap.
      - EURe refund (Gnosis EVM) – EVM address for EURe refund.
  - We prefill it with your own addresses:

    DEFAULT_EURE_EVM = 0x196C28928b1386D8Dcd32ab223bECcce6f731264
    DEFAULT_BTC_ADDR = 1LBiZCtkByR3BuH7K3RJA15fmri84NW6CT
  - When you click “Get deposit & start swap”:
      - The UI calls either:
          - POST /api/intend/btc-to-eure
          - POST /api/intend/eure-to-btc
      - The server calls 1‑Click /v0/quote with swapType: EXACT_INPUT.
      - On success, you get:
          - amountInFormatted (nice units).
          - amountOutFormatted (approx receive).
          - A depositAddress on BTC or Gnosis.
          - A deadline.
      - The UI shows:
          - A summary (“You send / You receive”).
          - The deposit address.
          - A QR code for wallet apps.
          - A “status pill” that polls execution via GET
/api/intend/status/:depositAddress.

  ### /intent/intend/: Advanced Tester

  This page is for debugging and power users:

  - Quick test buttons:
      - “Test: 10,000 sats → EURe”
      - “Test: 10 EURe → BTC”
  - A custom form similar to /intent/ but with simple text inputs.
  - On every quote attempt:
      - Shows a success box with the same info as /intent/.
      - Or shows the raw error from 1‑Click, including:

        {
          "message": "...",
          "status": 400,
          "bodyMessage": "Failed to get quote",
          "correlationId": "...",
          "requestBody": { ...full JSON sent to /v0/quote... }
        }
  - At the bottom, a “Recent swaps (this server)” section:
      - Backed by GET /api/intend/history.
      - Based purely on swaps initiated via this UI/server.
      - Shows direction, timestamp, amount in/out, and deposit address.

  ———

  ## 3. The UI Server: Intents & History

  The server (server/index.ts) runs on port 4100 and does three things:

  1. Quote + Intend endpoints (EXACT_INPUT)
      - POST /api/intend/btc-to-eure:
          - Validates amountInSats, recipientEvm, refundBtc.
          - Calls quoteExactInputBtcToEure which uses 1‑Click’s getQuote with:
              - originAsset = nep141:btc.omft.near
              - destinationAsset = EURe
              - amount = satsIn
              - refundTo = refundBtc (BTC).
              - recipient = recipientEvm (Gnosis).
          - Returns deposit address + amounts.
      - POST /api/intend/eure-to-btc:
          - Validates amountInEure, recipientBtc, refundEvm.
          - Converts EURe decimal → 18‑decimals (toUnits).
          - Calls getQuote with origin/destination reversed.

     For each successful intend quote, it appends an IntentLogItem to
an in‑memory intentLog:

     type IntentLogItem = {
       direction: 'btc-to-eure' | 'eure-to-btc';
       depositAddress: string;
       createdAt: string;
       amountIn: string;
       amountInFormatted: string;
       amountOut: string;
       amountOutFormatted: string;
       test?: boolean;
       recipient?: string;
       refund?: string;
     };
  2. History APIs
      - GET /api/intend/history:
          - Returns intentLog sorted newest‑first.
      - GET /api/intend/history/:depositAddress:
          - Returns:
              - The log entry for that deposit (if any), and
              - The execution status from 1‑Click getExecutionStatus.
  3. Status proxy
      - GET /api/intend/status/:depositAddress:
          - Straight proxy to 1‑Click getExecutionStatus, used by
/intent/ to update the status pill.

  ———

  ## 4. The AMM Solver: How We Provide Liquidity

  The solver is the official NEAR Intents AMM implementation,
configured for EURe ↔ BTC:

  - Tokens:

    AMM_TOKEN1_ID =
nep141:gnosis-0x420ca0f9b9b604ce0fd9c18ef134c705e5fa3430.omft.near
(EURe)
    AMM_TOKEN2_ID = nep141:btc.omft.near
              (BTC)
  - Environment highlights:

    NEAR_ACCOUNT_ID = nuri-solver.near
    NEAR_PRIVATE_KEY = ed25519:...
    RELAY_WS_URL = wss://solver-relay-v2.chaindefuser.com/ws
    ONE_CLICK_API_ONLY = true
    MARGIN_PERCENT = 0.3
  - Behavior:
      - On startup:
          - Connects to NEAR using near-api-js.
          - Loads reserves of EURe & BTC from the Intents contract.
          - Computes a deterministic nonce from reserves.
      - Via WebSocket:
          - Subscribes to:
              - QUOTE events (incoming quote requests).
              - QUOTE_STATUS events (executed intents).
          - Filters quotes only for the EURe/BTC pair.
      - For each quote request:
          - Checks it’s from a trusted partner (partner_id = 1click or
router-solver).
          - Computes the AMM price with margin.
          - Builds a NEP‑413 signed payload and sends a quote_response
back to the relay.

  The AMM math is constant‑product (x · y = k) with margin:

  - For EXACT_INPUT (user specifies amount in):

    amountInWithFee = amountIn * (1 – margin)
    out = (amountInWithFee * reserveOut) / (reserveIn + amountInWithFee)
  - For EXACT_OUTPUT (if used):

    in = reserveIn * out / ((reserveOut – out) * (1 – margin))

  The margin is set by MARGIN_PERCENT (0.3 by default).

  ———

  ## 5. How a BTC → EURe Swap Flows End‑to‑End

  Take a BTC → EURe swap from the /intent/ UI:

  1. User requests a quote
      - UI sends POST /api/intend/btc-to-eure with:
          - amountInSats
          - recipientEvm
          - refundBtc
      - UI server calls 1‑Click /v0/quote with swapType: EXACT_INPUT.
  2. 1‑Click asks solvers
      - 1‑Click forwards a quote request to the solver relay.
      - Relay broadcasts to all solvers that support the btc.omft.near
→ EURe pair.
  3. Our solver answers
      - Our solver sees a QUOTE event for nep141:btc.omft.near → EURe.
      - It:
          - Logs the request into recent_quotes.
          - Computes an EURe output with margin = 0.3%.
          - Signs a NEP‑413 quote.
          - Sends quote_response back to the relay.
  4. 1‑Click picks a quote
      - Once it has a quote, 1‑Click returns to our UI server:
          - The depositAddress (usually a BTC address).
          - amountIn, amountOut, formatted fields.
      - The UI server saves this in intentLog.
  5. User pays
      - The user sends BTC to the deposit address.
      - 1‑Click’s internal machinery:
          - Observes the BTC payment.
          - Creates a NEAR intent targeting intents.near.
          - Communicates with the relay and our solver quote to
execute the swap.
          - Sends EURe on Gnosis to recipientEvm.
  6. Status updates
      - UI polls GET /api/intend/status/:depositAddress every 5 seconds.
      - Solver receives QUOTE_STATUS events for intents that involve
its quote and:
          - Updates its reserves snapshot.
          - Logs them into recent_intents.
  7. Monitoring
      - On emino.app/solver/ the dashboard shows:
          - Reserves (our liquidity on intents.near).
          - Recent quotes and intents that went through the relay.
          - “Recent Swaps (via emino.app UI)” pulled from /api/intend/history.

  ———

  ## 6. How the 0.3% Margin Generates Revenue

  MARGIN_PERCENT = 0.3 means the solver takes 0.3% spread on each
swap, implemented inside the AMM.

  - For BTC → EURe:
      - The solver effectively takes 0.3% of the BTC input as “fee”
and only uses 99.7% of it to compute
        how much EURe to send.
      - That extra 0.3% stays inside the BTC reserve.
  - For EURe → BTC:
      - The fee is taken from the EURe input; 0.3% of EURe stays in
the EURe reserve.

  Over many swaps:

  - Both EURe and BTC reserves grow relative to what a fee‑less AMM would have.
  - That growth equals the cumulative margin – your solver revenue –
minus any losses from adverse price
    movements.
  - You can think of it as being the market maker: you earn the spread
(0.3%) but carry the risk if BTC/
    EURe price moves.

  ———

  ## 7. In Which Currency Do We Earn?

  On each individual swap, the margin is paid in the asset the user sends:

  - BTC → EURe:
      - Margin is in BTC; your BTC reserve goes up slightly more than
it would without fees.
  - EURe → BTC:
      - Margin is in EURe; your EURe reserve goes up.

  Over time:

  - You accumulate extra BTC when users send BTC and extra EURe when
users send EURe.
  - Your profit lives inside the reserves on the Intents contract.

  The solver dashboard’s “Reserves (on intents contract)” card shows
those reserves in human units (EURe
  and BTC) so you can see at a glance how much liquidity – and
implicitly profit – is sitting in the pool.

  ———

  ## 8. Depositing and Withdrawing Liquidity

  The AMM solver expects you to fund reserves in NEAR Intents before running:

  1. Preparation
      - Make sure your solver account (e.g. nuri-solver.near) has:
          - EURe tokens (on NEAR, the wrapped EURe).
          - BTC tokens (btc.omft.near) on NEAR.
      - Add the solver’s public key to intents.near (so it can sign quotes).
  2. Depositing tokens to Intents

     Using NEAR CLI (simplified outline):
      - Deposit EURe to intents.near on behalf of nuri-solver.near.
      - Deposit BTC to intents.near similarly.

     The exact commands depend on the NEP‑141 FT contracts you use
(ft_transfer_call / storage_deposit),
     and are described in NEAR Intents’ and the AMM solver’s README.
Conceptually, you’re moving tokens
     from your solver account into a reserve position on the Intents contract.
  3. Running the solver

     Once reserves are in place:

     AMM_TOKEN1_ID=...EURe...
     AMM_TOKEN2_ID=nep141:btc.omft.near
     NEAR_ACCOUNT_ID=nuri-solver.near
     NEAR_PRIVATE_KEY=ed25519:...
     RELAY_WS_URL=wss://solver-relay-v2.chaindefuser.com/ws
     APP_PORT=4010
     MARGIN_PERCENT=0.3
     ONE_CLICK_API_ONLY=true

     npm start

     When the solver starts:
      - emino.app/solver/ shows:
          - Health = READY
          - Reserves = non‑zero EURe & BTC.
          - Total supply, recent quotes/intents.
  4. Withdrawing / Taking Profit

     To realize profits, you can:
      - Reduce your reserve position on intents.near:
          - Withdraw part of the EURe/BTC reserves back to nuri-solver.near.
      - Bridge assets out:
          - Withdraw BTC from the NEAR BTC token into on‑chain BTC.
          - Withdraw EURe back to Gnosis, if desired.

     Again, the exact commands depend on the FT bridges and Intents
tooling, but the principle is: the
     “extra” BTC/EURe that has accumulated in the reserves (vs. your
initial deposit) is your PnL.

  ———

  ## 9. Monitoring: emino.app/solver/

  The solver dashboard is designed to answer three questions:

  1. Is our solver healthy and connected?
      - Health card:
          - ready: true/false
          - Solver account (ours): nuri-solver.near
      - Websocket card:
          - Connection to relay (CONNECTED / DISCONNECTED).
          - Last relay event timestamp.
  2. What liquidity do we have and what’s happening on NEAR?
      - Reserves:
          - EURe & BTC reserves in human units.
          - “Our liquidity on intents.near for this solver”.
      - Total supply:
          - Global EURe/BTC supply on NEAR Intents (all solvers).
  3. What activity is flowing through us vs. the network?
      - Recent Quotes (ours):
          - Only quotes calculated and signed by this solver.
      - Recent Swaps (via emino.app UI):
          - History from GET /api/intend/history.
          - Exactly what you see on /intent/intend/.
      - Recent Intents (network):
          - All intents observed via the relay.
          - Rows with asset/amount filled are intents that match our own quotes.
      - Recent Intents (details):
          - Same intents but with full hashes and timestamps for deep debugging.

  Together, this gives you:

  - “How busy is our solver?”
  - “Are quotes being accepted and executed?”
  - “Are users actually swapping via our UI?”
  - “How much liquidity do we still have?”

  ———

  ## 10. Where to Go Next

  Now that everything is wired and functioning end‑to‑end, we can
iterate in a few directions:

  - Better pricing policies
      - Adjust MARGIN_PERCENT by pair, size, or volatility.
      - Use external price feeds to keep the AMM centered around a fair price.
  - More pairs
      - Add additional tokens to the same solver or run multiple solvers.
  - Richer UI
      - Let users pick different swap sizes and see slippage and
effective price.
      - Add “expert mode” with raw request/response JSON embedded.

  For now, we already have:

  - A fully working BTC ↔ EURe cross‑chain swap via NEAR Intents & 1‑Click.
  - A custom AMM solver earning 0.3% margin on each swap.
  - Monitoring, history, and a clean separation between “our” data and
the broader NEAR Intents network.

  Feel free to share this post with anyone who wants to understand how
the system works under the hood or
  is curious how a solver can actually make money providing liquidity.

---
*Post created via email from emin@nuri.com*
