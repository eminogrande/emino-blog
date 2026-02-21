---
title: "microgpt.py (Karpathy) — Part 2: shapes at every step + a tiny forward pass"
date: 2026-02-15T22:05:00Z
draft: false
description: "Exact vector/matrix shapes through embeddings, attention, MLP, logits, loss, and how caching keys/values grows with time. Plus a tiny numeric toy forward pass."
categories: ["AI", "Programming", "Explainers"]
tags: ["Karpathy", "GPT", "Python", "Machine Learning", "Attention"]
slug: "microgpt-karpathy-part-2-shapes-and-a-tiny-forward-pass"
---

![](/media/microgpt-karpathy-part-2-shapes-and-a-tiny-forward-pass/cover.jpg)

This is a continuation of:
- **Part 1**: https://emino.app/posts/microgpt-karpathy-line-by-line/

Part 1 explained the script as a story. This Part 2 makes it *re-implementable* by being very explicit about **shapes**.

I’ll use the script’s default hyperparameters:

- `vocab_size = V`
- `block_size = T = 16`
- `n_embd = C = 16`
- `n_head = H = 4`
- `head_dim = D = C/H = 4`
- `n_layer = L = 1`

When I write shapes I’ll use:

- vectors: `[C]`
- matrices: `[out, in]`
- sequences of vectors (time steps): `[t, C]`

---

## 1) Parameter shapes (what lives in `state_dict`)

### Embeddings

- Token embedding table `wte`: **`[V, C]`**
  - lookup with `token_id` gives a vector **`[C]`**
- Position embedding table `wpe`: **`[T, C]`**
  - lookup with `pos_id` gives a vector **`[C]`**

### Attention (per layer)

Each is a linear map from `[C] → [C]`:

- `attn_wq`: **`[C, C]`**
- `attn_wk`: **`[C, C]`**
- `attn_wv`: **`[C, C]`**
- `attn_wo`: **`[C, C]`**

### MLP (per layer)

Karpathy uses the classic 4× expansion:

- `mlp_fc1`: **`[4C, C]`**   (up-project)
- `mlp_fc2`: **`[C, 4C]`**   (down-project)

### LM head

- `lm_head`: **`[V, C]`**
  - maps hidden state `[C]` to logits `[V]`

---

## 2) The forward pass at one time step (one `pos_id`)

The script is "token-by-token" (one position at a time), but it still behaves like a normal Transformer because it keeps a **key/value cache**.

### 2.1 Embeddings

- `tok_emb = wte[token_id]` → **`[C]`**
- `pos_emb = wpe[pos_id]` → **`[C]`**
- `x = tok_emb + pos_emb` → **`[C]`**
- `x = rmsnorm(x)` → **`[C]`**

### 2.2 Compute Q, K, V

Each is a linear projection `[C] → [C]`:

- `q = x @ Wq` → **`[C]`**
- `k = x @ Wk` → **`[C]`**
- `v = x @ Wv` → **`[C]`**

Now the cache grows with time.

- Before appending, `keys[layer]` has length `pos_id` (0-based).
- After `keys[layer].append(k)`, it has length `pos_id+1`.

So at step `pos_id = t`, the cached keys/values are:

- `k_cache`: list of `t+1` vectors of shape `[C]` → conceptually **`[t+1, C]`**
- `v_cache`: list of `t+1` vectors of shape `[C]` → conceptually **`[t+1, C]`**

### 2.3 Split into heads

We slice the channel dimension into `H` heads.

- `q_h` → **`[D]`** for each head
- `k_h[t]` → **`[D]`** for each cached time `t`
- `v_h[t]` → **`[D]`**

### 2.4 Attention math (per head)

For a fixed head:

1) **Attention logits** for each cached time `t`:

- dot product: `q_h · k_h[t]` → scalar
- scale: divide by `sqrt(D)` → scalar

So you get a vector of logits:

- `attn_logits` → **`[t+1]`**

2) Softmax:

- `attn_weights = softmax(attn_logits)` → **`[t+1]`**

3) Weighted sum of values:

- `head_out[j] = Σ_t attn_weights[t] * v_h[t][j]`

Result:

- `head_out` → **`[D]`**

Do this for all heads and concatenate:

- `x_attn` → **`[C]`**

Then output projection:

- `x = x_attn @ Wo` → **`[C]`**
- residual add: `x = x + x_residual` → **`[C]`**

### 2.5 MLP block

- `x = rmsnorm(x)` → `[C]`
- `x = x @ fc1` → **`[4C]`**
- `x = relu(x)` → `[4C]`
- `x = x @ fc2` → **`[C]`**
- residual add: `[C]`

### 2.6 Logits

- `logits = x @ lm_head` → **`[V]`**

Then:

- `probs = softmax(logits)` → `[V]`
- loss for the target token: `-log(probs[target_id])` → scalar

---

## 3) A tiny numeric toy forward pass (not the real model)

The real model uses `C=16`, `H=4`, etc. That’s too big for a "by hand" demo.

So here is a **toy version** with the same structure:

- `C = 4`
- `H = 2`
- `D = 2`
- we assume we are at time `t=1` (so we have **two** cached tokens)

### Setup

Let the query for one head be:

- `q_h = [1, 0]`

Let cached keys be:

- `k_h[0] = [1, 0]`
- `k_h[1] = [0, 1]`

Dot products:

- `q·k[0] = 1`
- `q·k[1] = 0`

Scale by `sqrt(D)=sqrt(2) ≈ 1.414`:

- logits ≈ `[0.707, 0.0]`

Softmax:

- exp(0.707)=2.028, exp(0)=1.000
- sum=3.028
- weights ≈ `[0.67, 0.33]`

Let cached values be:

- `v_h[0] = [10, 0]`
- `v_h[1] = [0, 10]`

Weighted sum:

- output ≈ `0.67*[10,0] + 0.33*[0,10]`
- output ≈ `[6.7, 3.3]`

That’s what attention does: it mixes past value vectors based on similarity of query to keys.

---

## 4) What to implement first (if you’re rebuilding this)

If your goal is to reproduce microgpt.py, build in this order:

1) Tokenizer + BOS
2) `Value` autograd + `backward()`
3) `linear`, `softmax`, `rmsnorm`
4) single-head attention (get it working)
5) multi-head split/concat
6) MLP + residuals
7) LM head + NLL loss
8) Adam update
9) sampling loop

Once this works, optimize with NumPy/PyTorch.
