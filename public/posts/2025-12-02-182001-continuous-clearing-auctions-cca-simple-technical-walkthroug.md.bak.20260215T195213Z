+++
title = "Continuous Clearing Auctions (CCA): Simple + Technical Walkthrough"
date = 2025-12-02T18:20:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "continuous-clearing-auctions-cca-simple-technical-walkthroug"
+++


# Continuous Clearing Auctions (CCA): Simple + Technical Walkthrough

Below is a simplified, thread-style explanation (similar structure to the
screenshots), followed by a more technical appendix with math and a small
simulation.

---

## 1. Token Sales Are Generally Messy

Traditional token launches often look like this:

- A fixed launch time.
- Everyone tries to buy at once.
- Bots and fast traders usually win.
- The final “price” is unclear and volatile for the first hours or days.

This leads to:

- Over-paying by retail participants.
- Concentrated allocations in a few hands.
- Difficult price discovery and messy early trading.

---

## 2. The Old Token Launch Playbook

Common mechanisms and their issues:

1. **Fixed price sale**
- Project sets a price.
- If price is too low, it sells out instantly to bots and arbitrageurs.
- If too high, sale drags and looks unsuccessful.

2. **Dutch auction (price goes down over time)**
- Professional traders wait to buy as low as possible.
- Late sniping decides the outcome.
- Retail participants face a timing game they are not equipped for.

3. **One-shot uniform-price auction**
- Everyone submits bids once.
- The market clears at a single price.
- But it happens only at one moment in time, and liquidity must be set up
separately after.

4. **Direct AMM launch (e.g., immediate Uniswap pool)**
- Pool starts with thin liquidity.
- Early trades move the price a lot.
- MEV and mempool competition influence who gets good fills.

---

## 3. CCA Flips the Script (Simple View)

A **Continuous Clearing Auction (CCA)** changes the process:

- The sale is split into many **blocks** (time intervals).
- You **submit one bid** with:
- Max price you are willing to pay.
- Amount of tokens you want.
- The protocol automatically **spreads your bid across the whole sale**.
- At each block, it computes a **fair market price** based on all active
bids.
- Everyone who gets filled in that block pays **the same price**.

You:
- Do not have to click fast.
- Do not have to watch the price every second.
- Just specify your maximum willingness to pay and size.

---

## 4. Here’s the Core Mechanism

For each block:

1. The protocol has a fixed amount of tokens for that block.
2. It looks at all active bids and sorts them by **max price**.
3. It finds the **lowest price** at which total demand ≥ block supply.
4. That price is the **clearing price** for the block.
5. All bids with `P_max` at or above that clearing price are eligible.
6. If there is more demand than supply at that price, eligible bids are
**scaled pro-rata**.
7. Everyone who is filled pays that same clearing price.

This repeats on every block until the sale ends.

---

## 5. “What If I Bid Too High?”

The protocol enforces a **max price guarantee**:

- You choose `P_max` (the most you are willing to pay per token).
- If the block’s clearing price `P_clear` is **above** your `P_max`:
- Your bid is **not** executed in that block.
- Your bid slices remain available for later blocks or can be withdrawn as
the sale rules allow.

Result:
- You never pay more than `P_max`.
- If the market clears lower than your `P_max`, you simply get filled at
the **lower** clearing price.

---

## 6. The “Early Bird” Effect

In CCA:

- Bidding early means your order is spread over **more blocks**.
- That gives you more opportunities to be filled in blocks where the
clearing price is relatively low.
- If you wait until the last block:
- Your order only participates in the final blocks.
- You mostly see the **later, potentially more expensive** clearing prices.

So, unlike “fastest finger first,” the mechanism encourages:

- Early participation.
- Longer exposure to the full price discovery process.

---

## 7. When the Auction Ends

At the end of the sale:

1. The protocol has:
- A full record of all clearing prices and filled quantities per block.
- Total raised assets.
- Remaining unsold tokens (if any).

2. According to the configured rules:
- A portion of the raised assets and remaining tokens can be
**automatically deposited** into a **Uniswap v4 pool**.
- This seeds initial liquidity at a price consistent with the auction
outcome.

This avoids a separate “now we figure out liquidity” phase and gives:

- A clear history of price discovery.
- Immediate secondary trading with pre-funded liquidity.

---

## 8. Why This Matters (Conceptually)

CCA aims to:

- Separate **price discovery** from low-level mempool / latency games.
- Provide a **uniform price per block**, not per individual transaction.
- Make it harder for:
- Bots to front-run retail participants.
- Whales to dominate purely via speed.
- Provide a direct bridge from **token sale** → **liquidity bootstrapping**
on Uniswap v4.

It is still an auction:
- There is competition.
- Prices can go high or low.
- But the process is better structured and more transparent.

---

## 9. Technical Appendix: Simple Example With Math

To make the mechanism concrete, consider a **single-block** example (one
clearing event) first. A multi-block CCA just repeats this per block with
bid slices.

### 9.1 Assumptions

- Tokens available in this block: `S = 1,000`.
- 10 participants submit bids with:
- Maximum price `P_max`.
- Desired quantity `Q`.

### 9.2 Bids

| Participant | Max Price `P_max` | Quantity `Q` |
|------------|-------------------|--------------|
| A | 1.80 | 150 |
| B | 2.20 | 200 |
| C | 1.00 | 50 |
| D | 2.50 | 400 |
| E | 0.90 | 80 |
| F | 1.60 | 120 |
| G | 3.00 | 500 |
| H | 2.00 | 200 |
| I | 1.20 | 100 |
| J | 0.75 | 40 |

### 9.3 Build the Order Book

Sort by `P_max` descending and accumulate demand:

| Rank | Participant | `P_max` | `Q` | Cumulative Demand |
|------|-------------|---------|-----|-------------------|
| 1 | G | 3.00 | 500 | 500 |
| 2 | D | 2.50 | 400 | 900 |
| 3 | B | 2.20 | 200 | 1,100 |
| 4 | H | 2.00 | 200 | 1,300 |
| 5 | A | 1.80 | 150 | 1,450 |
| ... | others | ≤ 1.60 | ... | ... |

We first exceed the supply `S = 1,000` when including participant B.
Therefore the **clearing price** is:

\[
P_{\text{clear}} = 2.20
\]

Eligible bidders are those with `P_max ≥ 2.20`:

- G: wants 500
- D: wants 400
- B: wants 200

Total eligible demand:

\[
D_{\text{eligible}} = 500 + 400 + 200 = 1{,}100
\]

We must allocate only 1,000 tokens.
Scale all eligible bidders **pro-rata** by factor:

\[
\alpha = \frac{S}{D_{\text{eligible}}} = \frac{1{,}000}{1{,}100} \approx
0.909
\]

### 9.4 Final Allocations

| Participant | Demand `Q` | Allocation `Q × α` | Price Paid |
|------------|------------|--------------------|------------|
| G | 500 | 454.5 | 2.20 |
| D | 400 | 363.6 | 2.20 |
| B | 200 | 181.8 | 2.20 |

All other participants receive zero in this block:

- Their `P_max` is strictly below the clearing price.
- They pay nothing and keep their capital.

No one pays above their max, and everyone filled pays the **same** price.

In a real CCA:

- The auction is split into many blocks.
- Each original bid is sliced across blocks.
- The per-block logic above is applied repeatedly.
- Over time, bidders experience a **volume-weighted average** of the
clearing prices in the blocks where they are filled.

---

## 10. Short TL;DR

- You say how much you want and the most you’ll pay per token.
- The protocol spreads your bid across the sale.
- Each block computes a single fair price from all bids.
- If that price is at or below your max, you can be filled; if above, you
are skipped.
- Everyone filled in a block pays the same price.
- At the end, funds and tokens can automatically seed a Uniswap v4 pool.

---

## Sources

1. **Uniswap – Continuous Clearing Auctions: Bootstrapping Liquidity on
Uniswap v4 (official blog)**
https://blog.uniswap.org/continuous-clearing-auctions

2. **Uniswap – Continuous Clearing Auctions Product Page**
https://cca.uniswap.org/en/

3. **Uniswap – Continuous Clearing Auction Smart-Contract Repository
(GitHub)**
https://github.com/Uniswap/continuous-clearing-auction

4. **Aztec Network – Auction Terms and Conditions**
https://aztec.network/auction-terms-conditions

5. **Markets.com – Continuous Clearing Auction: New Asset Price Discovery
With Uniswap and Aztec**
https://www.markets.com/news/continuous-clearing-auction-uniswap-aztec-2195-en

6. **The Defiant – Aztec Network Launches First Token Sale Using Uniswap’s
Continuous Clearing Auction**
https://thedefiant.io/news/defi/aztec-network-launches-first-token-sale-using-uniswaps-continuous-clearing-auction

7. **Algebra (Medium) – Continuous Clearing Auctions: A New Standard for
Fair Token Launches by Uniswap & Aztec**
https://medium.com/@crypto_algebra/continuous-clearing-auctions-a-new-standard-for-fair-token-launches-by-uniswap-aztec-739ba1767fd7

8. **Uniswap CCA Aztec Contract Instance (Etherscan)**
https://etherscan.io/address/0x608c4e792C65f5527B3f70715deA44d3b302F4Ee

9. **Panews – A Detailed Look at the Unique Features of Uniswap’s New CCA**
https://www.panewslab.com/en/articles/50611532-a7d8-4f14-ad67-b460319bc720

10. **Dennison Bertram – X Thread Explaining the Aztec CCA Sale**
https://x.com/dennisonbertram/status/1995911827171991948?s=46

---
*Post created via email from emin@nuri.com*
