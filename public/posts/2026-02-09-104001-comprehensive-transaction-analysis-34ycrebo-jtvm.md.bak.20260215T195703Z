+++
title = "Comprehensive Transaction Analysis: 34yCReBo...jtVM"
date = 2026-02-09T10:40:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "comprehensive-transaction-analysis-34ycrebo-jtvm"
markup = "markdown"
body_format = "markdown"
+++


# Comprehensive Transaction Analysis: 34yCReBo...jtVM

## 1. TRANSACTION IDENTITY
- **Transaction Hash:** 34yCReBoTyb12hH33xVdydoNJE5s58Kb1VeWYwY7jtVM
- **Blockchain:** NEAR Protocol (Mainnet)
- **Status:** Success (Finalized)
- **Signer (Sender):** v4v.near
- **Receiver Contract:** x.paras.near (The primary Paras marketplace contract)

---

## 2. FINANCIAL & GAS BREAKDOWN
| Item | Value (NEAR) | Value (USD approx.) | Description |
| :--- | :--- | :--- | :--- |
| **Gas Limit** | 300 TGas | N/A | Maximum computational units allocated. |
| **Gas Used** | 15.42 TGas | ~$0.00008 | Actual computational effort used. |
| **Transaction Fee** | 0.001542 NEAR | <$0.01 | The cost paid to
validators to process the call. |
| **Attached Deposit** | 1 yoctoNEAR | ~$0.0000...01 | A security
requirement for asset transfers. |

---

## 3. TECHNICAL ACTION: `mt_transfer_call`
The transaction executed a "Multi-Token Transfer and Call." This is a
high-level function that does two things simultaneously:
1.  **Transfer:** Moves ownership of a specific asset (defined by
NEP-245) from the sender to the receiver.
2.  **Call:** Tells the receiving contract to immediately perform a
secondary action (e.g., listing the item for sale or staking it).

---

## 4. NEP-245 EXPLAINED (MULTI-TOKEN STANDARD)
NEP-245 is the NEAR equivalent to Ethereum's **ERC-1155**. It is
designed to be a "Swiss Army Knife" for digital assets.

### Why it was used here:
- **Efficiency:** Instead of having different standards for
one-of-a-kind items (NFTs) and stackable items (Fungible tokens),
NEP-245 handles both in one contract.
- **Semi-Fungibility:** It allows for "Editions." For example, if an
artist releases 100 identical copies of a digital card, NEP-245 tracks
them as a single ID with a balance of 100, rather than 100 separate
unique entries.
- **Lower Costs:** Batch transfers are possible, allowing you to move
50 different items in one transaction fee.

---

## 5. EVENT LOGS & INTERNAL OPERATIONS
Inside this transaction, the following logic was triggered:
- **Standard:** `nep245`
- **Event:** `mt_transfer`
- **Logic Flow:**
  1. The contract verifies the sender (`v4v.near`) owns the `token_id`.
  2. The contract checks if the 1 yoctoNEAR deposit is present (security check).
  3. The balance of the `token_id` is subtracted from the sender and
added to the receiver.
  4. The `on_mt_transfer` callback is triggered on the receiver
contract to confirm it has "accepted" the assets.

---

## 6. SUMMARY
This transaction was an efficient, low-cost move of a digital asset on
the Paras marketplace. You paid a negligible fee (~$0.00008) to move a
token that supports the modern NEP-245 standard, ensuring the
marketplace could instantly recognize and process the transfer for its
next step (likely a trade or listing).

---
*Post created via email from emin@nuri.com*
