---
title: "microgpt.py explained in plain English (line by line)"
date: 2026-02-15T21:47:02Z
draft: false
categories: ["AI", "Programming"]
tags: ["GPT", "Karpathy", "Python", "Explained"]
slug: "microgpt-line-by-line-plain-english"
---

# microgpt.py explained in plain English (line by line)

This post rewrites the code **line by line** into plain English. The original code is by Andrej Karpathy (gist link below).

- Original gist: https://gist.github.com/karpathy/8627fe009c40f57531cb18360106ce95

---

## The code

```python
"""
The most atomic way to train and inference a GPT in pure, dependency-free Python.
This file is the complete algorithm.
Everything else is just efficiency.

@karpathy
"""

import os       # os.path.exists
import math     # math.log, math.exp
import random   # random.seed, random.choices, random.gauss, random.shuffle
random.seed(42) # Let there be order among chaos

# Let there be an input dataset `docs`: list[str] of documents (e.g. a dataset of names)
if not os.path.exists('input.txt'):
    import urllib.request
    names_url = 'https://raw.githubusercontent.com/karpathy/makemore/refs/heads/master/names.txt'
    urllib.request.urlretrieve(names_url, 'input.txt')
docs = [l.strip() for l in open('input.txt').read().strip().split('\n') if l.strip()] # list[str] of documents
random.shuffle(docs)
print(f"num docs: {len(docs)}")

# Let there be a Tokenizer to translate strings to discrete symbols and back
uchars = sorted(set(''.join(docs))) # unique characters in the dataset become token ids 0..n-1
BOS = len(uchars) # token id for the special Beginning of Sequence (BOS) token
vocab_size = len(uchars) + 1 # total number of unique tokens, +1 is for BOS
print(f"vocab size: {vocab_size}")

# Let there be Autograd, to recursively apply the chain rule through a computation graph
class Value:
    __slots__ = ('data', 'grad', '_children', '_local_grads') # Python optimization for memory usage

    def __init__(self, data, children=(), local_grads=()):
        self.data = data                # scalar value of this node calculated during forward pass
        self.grad = 0                   # derivative of the loss w.r.t. this node, calculated in backward pass
        self._children = children       # children of this node in the computation graph
        self._local_grads = local_grads # local derivative of this node w.r.t. its children

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data + other.data, (self, other), (1, 1))

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        return Value(self.data * other.data, (self, other), (other.data, self.data))

    def __pow__(self, other): return Value(self.data**other, (self,), (other * self.data**(other-1),))
    def log(self): return Value(math.log(self.data), (self,), (1/self.data,))
    def exp(self): return Value(math.exp(self.data), (self,), (math.exp(self.data),))
    def relu(self): return Value(max(0, self.data), (self,), (float(self.data > 0),))
    def __neg__(self): return self * -1
    def __radd__(self, other): return self + other
    def __sub__(self, other): return self + (-other)
    def __rsub__(self, other): return other + (-self)
    def __rmul__(self, other): return self * other
    def __truediv__(self, other): return self * other**-1
    def __rtruediv__(self, other): return other * self**-1

    def backward(self):
        topo = []
        visited = set()
        def build_topo(v):
            if v not in visited:
                visited.add(v)
                for child in v._children:
                    build_topo(child)
                topo.append(v)
        build_topo(self)
        self.grad = 1
        for v in reversed(topo):
            for child, local_grad in zip(v._children, v._local_grads):
                child.grad += local_grad * v.grad

# Initialize the parameters, to store the knowledge of the model.
n_embd = 16     # embedding dimension
n_head = 4      # number of attention heads
n_layer = 1     # number of layers
block_size = 16 # maximum sequence length
head_dim = n_embd // n_head # dimension of each head
matrix = lambda nout, nin, std=0.08: [[Value(random.gauss(0, std)) for _ in range(nin)] for _ in range(nout)]
state_dict = {'wte': matrix(vocab_size, n_embd), 'wpe': matrix(block_size, n_embd), 'lm_head': matrix(vocab_size, n_embd)}
for i in range(n_layer):
    state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)
    state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)
    state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)
params = [p for mat in state_dict.values() for row in mat for p in row] # flatten params into a single list[Value]
print(f"num params: {len(params)}")

# Define the model architecture: a stateless function mapping token sequence and parameters to logits over what comes next.
# Follow GPT-2, blessed among the GPTs, with minor differences: layernorm -> rmsnorm, no biases, GeLU -> ReLU
def linear(x, w):
    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]

def softmax(logits):
    max_val = max(val.data for val in logits)
    exps = [(val - max_val).exp() for val in logits]
    total = sum(exps)
    return [e / total for e in exps]

def rmsnorm(x):
    ms = sum(xi * xi for xi in x) / len(x)
    scale = (ms + 1e-5) ** -0.5
    return [xi * scale for xi in x]

def gpt(token_id, pos_id, keys, values):
    tok_emb = state_dict['wte'][token_id] # token embedding
    pos_emb = state_dict['wpe'][pos_id] # position embedding
    x = [t + p for t, p in zip(tok_emb, pos_emb)] # joint token and position embedding
    x = rmsnorm(x)

    for li in range(n_layer):
        # 1) Multi-head attention block
        x_residual = x
        x = rmsnorm(x)
        q = linear(x, state_dict[f'layer{li}.attn_wq'])
        k = linear(x, state_dict[f'layer{li}.attn_wk'])
        v = linear(x, state_dict[f'layer{li}.attn_wv'])
        keys[li].append(k)
        values[li].append(v)
        x_attn = []
        for h in range(n_head):
            hs = h * head_dim
            q_h = q[hs:hs+head_dim]
            k_h = [ki[hs:hs+head_dim] for ki in keys[li]]
            v_h = [vi[hs:hs+head_dim] for vi in values[li]]
            attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5 for t in range(len(k_h))]
            attn_weights = softmax(attn_logits)
            head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h))) for j in range(head_dim)]
            x_attn.extend(head_out)
        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])
        x = [a + b for a, b in zip(x, x_residual)]
        # 2) MLP block
        x_residual = x
        x = rmsnorm(x)
        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])
        x = [xi.relu() for xi in x]
        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])
        x = [a + b for a, b in zip(x, x_residual)]

    logits = linear(x, state_dict['lm_head'])
    return logits

# Let there be Adam, the blessed optimizer and its buffers
learning_rate, beta1, beta2, eps_adam = 0.01, 0.85, 0.99, 1e-8
m = [0.0] * len(params) # first moment buffer
v = [0.0] * len(params) # second moment buffer

# Repeat in sequence
num_steps = 1000 # number of training steps
for step in range(num_steps):

    # Take single document, tokenize it, surround it with BOS special token on both sides
    doc = docs[step % len(docs)]
    tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]
    n = min(block_size, len(tokens) - 1)

    # Forward the token sequence through the model, building up the computation graph all the way to the loss.
    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
    losses = []
    for pos_id in range(n):
        token_id, target_id = tokens[pos_id], tokens[pos_id + 1]
        logits = gpt(token_id, pos_id, keys, values)
        probs = softmax(logits)
        loss_t = -probs[target_id].log()
        losses.append(loss_t)
    loss = (1 / n) * sum(losses) # final average loss over the document sequence. May yours be low.

    # Backward the loss, calculating the gradients with respect to all model parameters.
    loss.backward()

    # Adam optimizer update: update the model parameters based on the corresponding gradients.
    lr_t = learning_rate * (1 - step / num_steps) # linear learning rate decay
    for i, p in enumerate(params):
        m[i] = beta1 * m[i] + (1 - beta1) * p.grad
        v[i] = beta2 * v[i] + (1 - beta2) * p.grad ** 2
        m_hat = m[i] / (1 - beta1 ** (step + 1))
        v_hat = v[i] / (1 - beta2 ** (step + 1))
        p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)
        p.grad = 0

    print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}")

# Inference: may the model babble back to us
temperature = 0.5 # in (0, 1], control the "creativity" of generated text, low to high
print("\n--- inference (new, hallucinated names) ---")
for sample_idx in range(20):
    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]
    token_id = BOS
    sample = []
    for pos_id in range(block_size):
        logits = gpt(token_id, pos_id, keys, values)
        probs = softmax([l / temperature for l in logits])
        token_id = random.choices(range(vocab_size), weights=[p.data for p in probs])[0]
        if token_id == BOS:
            break
        sample.append(uchars[token_id])
    print(f"sample {sample_idx+1:2d}: {''.join(sample)}")
```

---

## Line-by-line plain English

**Line 1:** `"""`
- Do this step as written (part of the algorithm’s mechanics).

**Line 2:** `The most atomic way to train and inference a GPT in pure, dependency-free Python.`
- Do this step as written (part of the algorithm’s mechanics).

**Line 3:** `This file is the complete algorithm.`
- Do this step as written (part of the algorithm’s mechanics).

**Line 4:** `Everything else is just efficiency.`
- Do this step as written (part of the algorithm’s mechanics).

**Line 5:** ``
- (blank line)

**Line 6:** `@karpathy`
- Do this step as written (part of the algorithm’s mechanics).

**Line 7:** `"""`
- Do this step as written (part of the algorithm’s mechanics).

**Line 8:** ``
- (blank line)

**Line 9:** `import os       # os.path.exists`
- Import the built-in Python module `os` so we can use it later. (Note: os.path.exists)

**Line 10:** `import math     # math.log, math.exp`
- Import the built-in Python module `math` so we can use it later. (Note: math.log, math.exp)

**Line 11:** `import random   # random.seed, random.choices, random.gauss, random.shuffle`
- Import the built-in Python module `random` so we can use it later. (Note: random.seed, random.choices, random.gauss, random.shuffle)

**Line 12:** `random.seed(42) # Let there be order among chaos`
- Set the random seed so results are reproducible (same random choices every run).

**Line 13:** ``
- (blank line)

**Line 14:** `# Let there be an input dataset \`docs\`: list[str] of documents (e.g. a dataset of names)`
- Let there be an input dataset `docs`: list[str] of documents (e.g. a dataset of names)

**Line 15:** `if not os.path.exists('input.txt'):`
- If the file does not exist yet, download or create it so we have input data.

**Line 16:** `    import urllib.request`
- Import the built-in Python module `urllib.request` so we can use it later.

**Line 17:** `    names_url = 'https://raw.githubusercontent.com/karpathy/makemore/refs/heads/master/names.txt'`
- Set/compute `names_url` (store a value in a variable).

**Line 18:** `    urllib.request.urlretrieve(names_url, 'input.txt')`
- Download a file from the internet and save it locally.

**Line 19:** `docs = [l.strip() for l in open('input.txt').read().strip().split('\n') if l.strip()] # list[str] of documents`
- Read the input file, split it into lines, clean them up, and store them as a list of documents (strings).

**Line 20:** `random.shuffle(docs)`
- Shuffle the documents so training sees them in random order.

**Line 21:** `print(f"num docs: {len(docs)}")`
- Print some information to the console so we can see what’s happening.

**Line 22:** ``
- (blank line)

**Line 23:** `# Let there be a Tokenizer to translate strings to discrete symbols and back`
- Let there be a Tokenizer to translate strings to discrete symbols and back

**Line 24:** `uchars = sorted(set(''.join(docs))) # unique characters in the dataset become token ids 0..n-1`
- Build the vocabulary: collect all unique characters used in the dataset and sort them.

**Line 25:** `BOS = len(uchars) # token id for the special Beginning of Sequence (BOS) token`
- Pick a special token id that represents “Beginning Of Sequence” (BOS).

**Line 26:** `vocab_size = len(uchars) + 1 # total number of unique tokens, +1 is for BOS`
- Compute the total vocabulary size (all characters plus the BOS token).

**Line 27:** `print(f"vocab size: {vocab_size}")`
- Print some information to the console so we can see what’s happening.

**Line 28:** ``
- (blank line)

**Line 29:** `# Let there be Autograd, to recursively apply the chain rule through a computation graph`
- Let there be Autograd, to recursively apply the chain rule through a computation graph

**Line 30:** `class Value:`
- Define a new class called `Value` (a custom data type).

**Line 31:** `    __slots__ = ('data', 'grad', '_children', '_local_grads') # Python optimization for memory usage`
- Set/compute `__slots__` (store a value in a variable).

**Line 32:** ``
- (blank line)

**Line 33:** `    def __init__(self, data, children=(), local_grads=()):`
- Define a function named `__init__` (a reusable block of code).

**Line 34:** `        self.data = data                # scalar value of this node calculated during forward pass`
- Set/compute `self.data` (store a value in a variable).

**Line 35:** `        self.grad = 0                   # derivative of the loss w.r.t. this node, calculated in backward pass`
- Set/compute `self.grad` (store a value in a variable).

**Line 36:** `        self._children = children       # children of this node in the computation graph`
- Set/compute `self._children` (store a value in a variable).

**Line 37:** `        self._local_grads = local_grads # local derivative of this node w.r.t. its children`
- Set/compute `self._local_grads` (store a value in a variable).

**Line 38:** ``
- (blank line)

**Line 39:** `    def __add__(self, other):`
- Define a function named `__add__` (a reusable block of code).

**Line 40:** `        other = other if isinstance(other, Value) else Value(other)`
- Set/compute `other` (store a value in a variable).

**Line 41:** `        return Value(self.data + other.data, (self, other), (1, 1))`
- Return a value from this function.

**Line 42:** ``
- (blank line)

**Line 43:** `    def __mul__(self, other):`
- Define a function named `__mul__` (a reusable block of code).

**Line 44:** `        other = other if isinstance(other, Value) else Value(other)`
- Set/compute `other` (store a value in a variable).

**Line 45:** `        return Value(self.data * other.data, (self, other), (other.data, self.data))`
- Return a value from this function.

**Line 46:** ``
- (blank line)

**Line 47:** `    def __pow__(self, other): return Value(self.data**other, (self,), (other * self.data**(other-1),))`
- Define a function named `__pow__` (a reusable block of code).

**Line 48:** `    def log(self): return Value(math.log(self.data), (self,), (1/self.data,))`
- Define a function named `log` (a reusable block of code).

**Line 49:** `    def exp(self): return Value(math.exp(self.data), (self,), (math.exp(self.data),))`
- Define a function named `exp` (a reusable block of code).

**Line 50:** `    def relu(self): return Value(max(0, self.data), (self,), (float(self.data > 0),))`
- Define a function named `relu` (a reusable block of code).

**Line 51:** `    def __neg__(self): return self * -1`
- Define a function named `__neg__` (a reusable block of code).

**Line 52:** `    def __radd__(self, other): return self + other`
- Define a function named `__radd__` (a reusable block of code).

**Line 53:** `    def __sub__(self, other): return self + (-other)`
- Define a function named `__sub__` (a reusable block of code).

**Line 54:** `    def __rsub__(self, other): return other + (-self)`
- Define a function named `__rsub__` (a reusable block of code).

**Line 55:** `    def __rmul__(self, other): return self * other`
- Define a function named `__rmul__` (a reusable block of code).

**Line 56:** `    def __truediv__(self, other): return self * other**-1`
- Define a function named `__truediv__` (a reusable block of code).

**Line 57:** `    def __rtruediv__(self, other): return other * self**-1`
- Define a function named `__rtruediv__` (a reusable block of code).

**Line 58:** ``
- (blank line)

**Line 59:** `    def backward(self):`
- Define a function named `backward` (a reusable block of code).

**Line 60:** `        topo = []`
- Set/compute `topo` (store a value in a variable).

**Line 61:** `        visited = set()`
- Set/compute `visited` (store a value in a variable).

**Line 62:** `        def build_topo(v):`
- Define a function named `build_topo` (a reusable block of code).

**Line 63:** `            if v not in visited:`
- Check a condition; if it’s true, run the indented block below.

**Line 64:** `                visited.add(v)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 65:** `                for child in v._children:`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 66:** `                    build_topo(child)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 67:** `                topo.append(v)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 68:** `        build_topo(self)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 69:** `        self.grad = 1`
- Set/compute `self.grad` (store a value in a variable).

**Line 70:** `        for v in reversed(topo):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 71:** `            for child, local_grad in zip(v._children, v._local_grads):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 72:** `                child.grad += local_grad * v.grad`
- Set/compute `child.grad +` (store a value in a variable).

**Line 73:** ``
- (blank line)

**Line 74:** `# Initialize the parameters, to store the knowledge of the model.`
- Initialize the parameters, to store the knowledge of the model.

**Line 75:** `n_embd = 16     # embedding dimension`
- Set/compute `n_embd` (store a value in a variable).

**Line 76:** `n_head = 4      # number of attention heads`
- Set/compute `n_head` (store a value in a variable).

**Line 77:** `n_layer = 1     # number of layers`
- Set/compute `n_layer` (store a value in a variable).

**Line 78:** `block_size = 16 # maximum sequence length`
- Set/compute `block_size` (store a value in a variable).

**Line 79:** `head_dim = n_embd // n_head # dimension of each head`
- Set/compute `head_dim` (store a value in a variable).

**Line 80:** `matrix = lambda nout, nin, std=0.08: [[Value(random.gauss(0, std)) for _ in range(nin)] for _ in range(nout)]`
- Set/compute `matrix` (store a value in a variable).

**Line 81:** `state_dict = {'wte': matrix(vocab_size, n_embd), 'wpe': matrix(block_size, n_embd), 'lm_head': matrix(vocab_size, n_embd)}`
- Set/compute `state_dict` (store a value in a variable).

**Line 82:** `for i in range(n_layer):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 83:** `    state_dict[f'layer{i}.attn_wq'] = matrix(n_embd, n_embd)`
- Set/compute `state_dict[f'layer{i}.attn_wq']` (store a value in a variable).

**Line 84:** `    state_dict[f'layer{i}.attn_wk'] = matrix(n_embd, n_embd)`
- Set/compute `state_dict[f'layer{i}.attn_wk']` (store a value in a variable).

**Line 85:** `    state_dict[f'layer{i}.attn_wv'] = matrix(n_embd, n_embd)`
- Set/compute `state_dict[f'layer{i}.attn_wv']` (store a value in a variable).

**Line 86:** `    state_dict[f'layer{i}.attn_wo'] = matrix(n_embd, n_embd)`
- Set/compute `state_dict[f'layer{i}.attn_wo']` (store a value in a variable).

**Line 87:** `    state_dict[f'layer{i}.mlp_fc1'] = matrix(4 * n_embd, n_embd)`
- Set/compute `state_dict[f'layer{i}.mlp_fc1']` (store a value in a variable).

**Line 88:** `    state_dict[f'layer{i}.mlp_fc2'] = matrix(n_embd, 4 * n_embd)`
- Set/compute `state_dict[f'layer{i}.mlp_fc2']` (store a value in a variable).

**Line 89:** `params = [p for mat in state_dict.values() for row in mat for p in row] # flatten params into a single list[Value]`
- Set/compute `params` (store a value in a variable).

**Line 90:** `print(f"num params: {len(params)}")`
- Print some information to the console so we can see what’s happening.

**Line 91:** ``
- (blank line)

**Line 92:** `# Define the model architecture: a stateless function mapping token sequence and parameters to logits over what comes next.`
- Define the model architecture: a stateless function mapping token sequence and parameters to logits over what comes next.

**Line 93:** `# Follow GPT-2, blessed among the GPTs, with minor differences: layernorm -> rmsnorm, no biases, GeLU -> ReLU`
- Follow GPT-2, blessed among the GPTs, with minor differences: layernorm -> rmsnorm, no biases, GeLU -> ReLU

**Line 94:** `def linear(x, w):`
- Define a function named `linear` (a reusable block of code).

**Line 95:** `    return [sum(wi * xi for wi, xi in zip(wo, x)) for wo in w]`
- Return a value from this function.

**Line 96:** ``
- (blank line)

**Line 97:** `def softmax(logits):`
- Define a function named `softmax` (a reusable block of code).

**Line 98:** `    max_val = max(val.data for val in logits)`
- Set/compute `max_val` (store a value in a variable).

**Line 99:** `    exps = [(val - max_val).exp() for val in logits]`
- Set/compute `exps` (store a value in a variable).

**Line 100:** `    total = sum(exps)`
- Set/compute `total` (store a value in a variable).

**Line 101:** `    return [e / total for e in exps]`
- Return a value from this function.

**Line 102:** ``
- (blank line)

**Line 103:** `def rmsnorm(x):`
- Define a function named `rmsnorm` (a reusable block of code).

**Line 104:** `    ms = sum(xi * xi for xi in x) / len(x)`
- Set/compute `ms` (store a value in a variable).

**Line 105:** `    scale = (ms + 1e-5) ** -0.5`
- Set/compute `scale` (store a value in a variable).

**Line 106:** `    return [xi * scale for xi in x]`
- Return a value from this function.

**Line 107:** ``
- (blank line)

**Line 108:** `def gpt(token_id, pos_id, keys, values):`
- Define a function named `gpt` (a reusable block of code).

**Line 109:** `    tok_emb = state_dict['wte'][token_id] # token embedding`
- Set/compute `tok_emb` (store a value in a variable).

**Line 110:** `    pos_emb = state_dict['wpe'][pos_id] # position embedding`
- Set/compute `pos_emb` (store a value in a variable).

**Line 111:** `    x = [t + p for t, p in zip(tok_emb, pos_emb)] # joint token and position embedding`
- Set/compute `x` (store a value in a variable).

**Line 112:** `    x = rmsnorm(x)`
- Set/compute `x` (store a value in a variable).

**Line 113:** ``
- (blank line)

**Line 114:** `    for li in range(n_layer):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 115:** `        # 1) Multi-head attention block`
- 1) Multi-head attention block

**Line 116:** `        x_residual = x`
- Set/compute `x_residual` (store a value in a variable).

**Line 117:** `        x = rmsnorm(x)`
- Set/compute `x` (store a value in a variable).

**Line 118:** `        q = linear(x, state_dict[f'layer{li}.attn_wq'])`
- Set/compute `q` (store a value in a variable).

**Line 119:** `        k = linear(x, state_dict[f'layer{li}.attn_wk'])`
- Set/compute `k` (store a value in a variable).

**Line 120:** `        v = linear(x, state_dict[f'layer{li}.attn_wv'])`
- Set/compute `v` (store a value in a variable).

**Line 121:** `        keys[li].append(k)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 122:** `        values[li].append(v)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 123:** `        x_attn = []`
- Set/compute `x_attn` (store a value in a variable).

**Line 124:** `        for h in range(n_head):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 125:** `            hs = h * head_dim`
- Set/compute `hs` (store a value in a variable).

**Line 126:** `            q_h = q[hs:hs+head_dim]`
- Set/compute `q_h` (store a value in a variable).

**Line 127:** `            k_h = [ki[hs:hs+head_dim] for ki in keys[li]]`
- Set/compute `k_h` (store a value in a variable).

**Line 128:** `            v_h = [vi[hs:hs+head_dim] for vi in values[li]]`
- Set/compute `v_h` (store a value in a variable).

**Line 129:** `            attn_logits = [sum(q_h[j] * k_h[t][j] for j in range(head_dim)) / head_dim**0.5 for t in range(len(k_h))]`
- Set/compute `attn_logits` (store a value in a variable).

**Line 130:** `            attn_weights = softmax(attn_logits)`
- Set/compute `attn_weights` (store a value in a variable).

**Line 131:** `            head_out = [sum(attn_weights[t] * v_h[t][j] for t in range(len(v_h))) for j in range(head_dim)]`
- Set/compute `head_out` (store a value in a variable).

**Line 132:** `            x_attn.extend(head_out)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 133:** `        x = linear(x_attn, state_dict[f'layer{li}.attn_wo'])`
- Set/compute `x` (store a value in a variable).

**Line 134:** `        x = [a + b for a, b in zip(x, x_residual)]`
- Set/compute `x` (store a value in a variable).

**Line 135:** `        # 2) MLP block`
- 2) MLP block

**Line 136:** `        x_residual = x`
- Set/compute `x_residual` (store a value in a variable).

**Line 137:** `        x = rmsnorm(x)`
- Set/compute `x` (store a value in a variable).

**Line 138:** `        x = linear(x, state_dict[f'layer{li}.mlp_fc1'])`
- Set/compute `x` (store a value in a variable).

**Line 139:** `        x = [xi.relu() for xi in x]`
- Set/compute `x` (store a value in a variable).

**Line 140:** `        x = linear(x, state_dict[f'layer{li}.mlp_fc2'])`
- Set/compute `x` (store a value in a variable).

**Line 141:** `        x = [a + b for a, b in zip(x, x_residual)]`
- Set/compute `x` (store a value in a variable).

**Line 142:** ``
- (blank line)

**Line 143:** `    logits = linear(x, state_dict['lm_head'])`
- Set/compute `logits` (store a value in a variable).

**Line 144:** `    return logits`
- Return a value from this function.

**Line 145:** ``
- (blank line)

**Line 146:** `# Let there be Adam, the blessed optimizer and its buffers`
- Let there be Adam, the blessed optimizer and its buffers

**Line 147:** `learning_rate, beta1, beta2, eps_adam = 0.01, 0.85, 0.99, 1e-8`
- Set/compute `learning_rate, beta1, beta2, eps_adam` (store a value in a variable).

**Line 148:** `m = [0.0] * len(params) # first moment buffer`
- Set/compute `m` (store a value in a variable).

**Line 149:** `v = [0.0] * len(params) # second moment buffer`
- Set/compute `v` (store a value in a variable).

**Line 150:** ``
- (blank line)

**Line 151:** `# Repeat in sequence`
- Repeat in sequence

**Line 152:** `num_steps = 1000 # number of training steps`
- Set/compute `num_steps` (store a value in a variable).

**Line 153:** `for step in range(num_steps):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 154:** ``
- (blank line)

**Line 155:** `    # Take single document, tokenize it, surround it with BOS special token on both sides`
- Take single document, tokenize it, surround it with BOS special token on both sides

**Line 156:** `    doc = docs[step % len(docs)]`
- Set/compute `doc` (store a value in a variable).

**Line 157:** `    tokens = [BOS] + [uchars.index(ch) for ch in doc] + [BOS]`
- Set/compute `tokens` (store a value in a variable).

**Line 158:** `    n = min(block_size, len(tokens) - 1)`
- Set/compute `n` (store a value in a variable).

**Line 159:** ``
- (blank line)

**Line 160:** `    # Forward the token sequence through the model, building up the computation graph all the way to the loss.`
- Forward the token sequence through the model, building up the computation graph all the way to the loss.

**Line 161:** `    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]`
- Set/compute `keys, values` (store a value in a variable).

**Line 162:** `    losses = []`
- Set/compute `losses` (store a value in a variable).

**Line 163:** `    for pos_id in range(n):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 164:** `        token_id, target_id = tokens[pos_id], tokens[pos_id + 1]`
- Set/compute `token_id, target_id` (store a value in a variable).

**Line 165:** `        logits = gpt(token_id, pos_id, keys, values)`
- Set/compute `logits` (store a value in a variable).

**Line 166:** `        probs = softmax(logits)`
- Set/compute `probs` (store a value in a variable).

**Line 167:** `        loss_t = -probs[target_id].log()`
- Set/compute `loss_t` (store a value in a variable).

**Line 168:** `        losses.append(loss_t)`
- Do this step as written (part of the algorithm’s mechanics).

**Line 169:** `    loss = (1 / n) * sum(losses) # final average loss over the document sequence. May yours be low.`
- Set/compute `loss` (store a value in a variable).

**Line 170:** ``
- (blank line)

**Line 171:** `    # Backward the loss, calculating the gradients with respect to all model parameters.`
- Backward the loss, calculating the gradients with respect to all model parameters.

**Line 172:** `    loss.backward()`
- Do this step as written (part of the algorithm’s mechanics).

**Line 173:** ``
- (blank line)

**Line 174:** `    # Adam optimizer update: update the model parameters based on the corresponding gradients.`
- Adam optimizer update: update the model parameters based on the corresponding gradients.

**Line 175:** `    lr_t = learning_rate * (1 - step / num_steps) # linear learning rate decay`
- Set/compute `lr_t` (store a value in a variable).

**Line 176:** `    for i, p in enumerate(params):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 177:** `        m[i] = beta1 * m[i] + (1 - beta1) * p.grad`
- Set/compute `m[i]` (store a value in a variable).

**Line 178:** `        v[i] = beta2 * v[i] + (1 - beta2) * p.grad ** 2`
- Set/compute `v[i]` (store a value in a variable).

**Line 179:** `        m_hat = m[i] / (1 - beta1 ** (step + 1))`
- Set/compute `m_hat` (store a value in a variable).

**Line 180:** `        v_hat = v[i] / (1 - beta2 ** (step + 1))`
- Set/compute `v_hat` (store a value in a variable).

**Line 181:** `        p.data -= lr_t * m_hat / (v_hat ** 0.5 + eps_adam)`
- Set/compute `p.data -` (store a value in a variable).

**Line 182:** `        p.grad = 0`
- Set/compute `p.grad` (store a value in a variable).

**Line 183:** ``
- (blank line)

**Line 184:** `    print(f"step {step+1:4d} / {num_steps:4d} | loss {loss.data:.4f}")`
- Print some information to the console so we can see what’s happening.

**Line 185:** ``
- (blank line)

**Line 186:** `# Inference: may the model babble back to us`
- Inference: may the model babble back to us

**Line 187:** `temperature = 0.5 # in (0, 1], control the "creativity" of generated text, low to high`
- Set/compute `temperature` (store a value in a variable).

**Line 188:** `print("\n--- inference (new, hallucinated names) ---")`
- Print some information to the console so we can see what’s happening.

**Line 189:** `for sample_idx in range(20):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 190:** `    keys, values = [[] for _ in range(n_layer)], [[] for _ in range(n_layer)]`
- Set/compute `keys, values` (store a value in a variable).

**Line 191:** `    token_id = BOS`
- Set/compute `token_id` (store a value in a variable).

**Line 192:** `    sample = []`
- Set/compute `sample` (store a value in a variable).

**Line 193:** `    for pos_id in range(block_size):`
- Start a loop: repeat the next indented block for each item in a collection.

**Line 194:** `        logits = gpt(token_id, pos_id, keys, values)`
- Set/compute `logits` (store a value in a variable).

**Line 195:** `        probs = softmax([l / temperature for l in logits])`
- Set/compute `probs` (store a value in a variable).

**Line 196:** `        token_id = random.choices(range(vocab_size), weights=[p.data for p in probs])[0]`
- Set/compute `token_id` (store a value in a variable).

**Line 197:** `        if token_id == BOS:`
- Check a condition; if it’s true, run the indented block below.

**Line 198:** `            break`
- Do this step as written (part of the algorithm’s mechanics).

**Line 199:** `        sample.append(uchars[token_id])`
- Do this step as written (part of the algorithm’s mechanics).

**Line 200:** `    print(f"sample {sample_idx+1:2d}: {''.join(sample)}")`
- Print some information to the console so we can see what’s happening.
