+++
title = "How to start your own near solver: chart, technical bits (env, keys, services, deployment)"
date = 2025-12-02T08:55:02Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "how-to-start-your-own-near-solver-chart-technical-bits-env-k"
+++


## 1. What this solver is and why it exists

  - The Near Intents protocol lets users express “I want to swap X for Y
under conditions Z” as intents.
  - A solver (this app) watches intents and acts as a market maker:
      - Keeps track of an on‑chain AMM pool (reserves for two NEP‑141
tokens).
      - Computes prices + margin for that pair.
      - When an intent is profitable (given your margin), it executes the
swap via your NEAR account.
  - The solver also exposes:
      - An HTTP status API (/status).
      - A dashboard (/dashboard) that shows health, reserves, quotes,
intents, balances.

  Your instance right now:

  - Runs as pm2 process near-solver, listening on 127.0.0.1:4010.
  - Is reachable via:
      - https://emino.app/status (JSON health).
      - https://emino.app/solver/ (dashboard UI).
  - ready:true and ws_connected:true → the solver is live and processing
relay traffic.

  ———

  ## 2. Walking through the components in the chart

  ### 2.1 User → Nginx → Solver

  - A user opens https://emino.app/solver/ in a browser.
  - Nginx vhost (emino.app):
      - Terminates TLS using a Let’s Encrypt certificate.
      - Has locations:
          - /solver/ → proxy_pass http://127.0.0.1:4010/dashboard
          - /status → proxy_pass http://127.0.0.1:4010/status
  - The browser:
      - Loads the HTML dashboard from /dashboard.
      - The inline JS immediately calls /status and then polls it every few
seconds for live data.
  - The solver’s HttpService builds the payload for /status and renders the
dashboard template for /
    dashboard.

  ### 2.2 The solver process (Node.js, pm2)

  The process is started roughly as:

  NODE_ENV=local pm2 start "npm start" --name near-solver

  - npm start runs:
    node -r tsconfig-paths/register -r ts-node/register src/main.ts

  The important files:

  - src/main.ts
      - Calls loadEnv() (from src/utils/load-env.ts).
      - Then require('./app').app().
  - src/utils/load-env.ts
      - Calls dotenv.config with:
          - path: ./env/.env.local (because NODE_ENV=local).
      - Validates process.env against a Joi schema
(src/configs/env.validation.ts).
      - Throws if anything required is missing/invalid.
      - Copies validated values back into process.env.
  - src/app.ts
      - Instantiates services:

        const cacheService   = new CacheService();
        const nearService    = new NearService(); await nearService.init();
        const intentsService = new IntentsService(nearService);
        const quoterService  = new QuoterService(cacheService, nearService,
intentsService);
        await quoterService.updateCurrentState();
        const cronService    = new CronService(quoterService);
cronService.start();
        const websocketSvc   = new
WebsocketConnectionService(quoterService, cacheService);
  websocketSvc.start();
        const httpService    = new HttpService(cacheService, quoterService,
nearService);
  httpService.start();
      - This gives you:
          - Live NEAR connection.
          - AMM pricing + state.
          - WebSocket stream from the solver relay.
          - Periodic state refresh.
          - HTTP API.

  ### 2.3 Services and their roles

  NearService

  - Uses near-api-js to construct connections:
      - Network: NEAR_NETWORK_ID (mainnet or testnet).
      - Node URLs: from NEAR_NODE_URLS or NEAR_NODE_URL, or defaults:
          - Mainnet: https://free.rpc.fastnear.com, https://near.lava.build
          - Testnet: https://test.rpc.fastnear.com, https://neart.lava.build
  - Loads solver identity from env:
      - NEAR_ACCOUNT_ID – your solver account, e.g. my-solver.near.
      - NEAR_PRIVATE_KEY – an ed25519:... key string for that account.
  - Exposes helpers:
      - getBalance() – to show how much NEAR the solver holds (gas +
liquidity).
      - Make view calls / send signed transactions against NEAR contracts.

  IntentsService

  - Wraps the intents contract API (INTENTS_CONTRACT env if used).
  - Lets the solver:
      - Read pool data / reserves.
      - Interact with intents (e.g., settlement logic).

  QuoterService

  - Knows:
      - The two token IDs (from AMM_TOKEN1_ID / AMM_TOKEN2_ID).
      - The margin you want: MARGIN_PERCENT (e.g. 0.3 = 0.3%).
  - Maintains an internal state snapshot:
      - Reserves for each NEP‑141 token.
      - Any other AMM parameters needed.
  - Methods:
      - updateCurrentState() – fetches fresh on‑chain pool state via
NearService and IntentsService.
      - Methods invoked by WebSocket events to adjust state per new
quotes/intents.
  - Quoter decides whether a given intent is worth executing given your
current pool and margin.

  CacheService

  - In‑memory key‑value cache.
  - Keys you’ll see:
      - ws_connected – boolean.
      - ws_last_event_at – timestamp of last relay event.
      - reserves – current pool reserves.
      - reserves_updated_at – when reserves were last refreshed.
      - recent_quotes – list of latest quotes.
      - recent_intents – list of latest intents with tx hashes.
      - total_supply – cached for 60s so you don’t spam NEAR RPC.

  WebsocketConnectionService

  - Connects to the solver relay:
      - RELAY_WS_URL – e.g. wss://solver-relay-v2.chaindefuser.com/ws.
      - RELAY_AUTH_KEY – a JWT / auth token issued by the relay operator.
  - Behavior:
      - Opens a WebSocket.
      - Authenticates using the auth key.
      - Receives:
          - New quotes (price offers).
          - New intents (user swap requests).
          - Execution/settlement updates.
      - For each event:
          - Updates CacheService with recent quotes/intents and timestamps.
          - Tells QuoterService about relevant changes so prices and state
are fresh.

  CronService

  - Runs a periodic job (e.g. every 5–10 seconds depending on
implementation) that:
      - Calls QuoterService.updateCurrentState().
      - Ensures that even if WebSocket traffic stutters, the solver’s
picture of the pool stays correct.

  HttpService

  - Pure Node http server; no Express.
  - Listens on APP_PORT (in your case 4010).
  - Routes:
      - / – simple JSON: { ready: true }
      - /status – builds a full status payload:
          - ready – constant true if process is up.
          - ws_connected, ws_last_event_at.
          - reserves + reserves_updated_at.
          - margin_percent.
          - recent_quotes, recent_intents.
          - deposit_addresses – BTC + EURe deposit addresses.
          - near_balance – yocto NEAR.
          - near_balance_near – human-readable NEAR via a formatYocto
helper.
          - total_supply – token supplies via ft_total_supply view calls.
      - /dashboard – returns a static HTML page with embedded JS:
          - Injects bootstrap data = current /status JSON.
          - Injects the list of token IDs and token meta (symbols,
decimals).
          - Renders a grid of cards:
              - Health + readiness.
              - Deposit addresses.
              - WebSocket status.
              - Reserves on the intents contract.
              - Total supply on NEAR.
              - Recent quotes.
              - Recent intents.
          - Starts a loop that re‑calls /status every few seconds and
updates the UI.

  ———

  ## 3. External systems

  The solver doesn’t live in isolation; it’s part of this broader system:

  - Solver relay (RELAY_WS_URL):
      - A central hub that feeds intents and quotes to registered solvers.
      - You authenticate via RELAY_AUTH_KEY.
      - Solvers send signed transactions that correspond to accepted
intents.
  - NEAR RPC nodes:
      - Used for:
          - View calls (e.g. ft_total_supply, pool state).
          - Sending transactions from NEAR_ACCOUNT_ID.
      - The solver uses multiple URLs for redundancy and simple failover.
  - Intents contract (INTENTS_CONTRACT):
      - Holds the logic and pools for EURe/BTC (and other pairs).
      - Manages reserves and settlement.
  - Deposit addresses (off-chain bridge):
      - BTC mainnet address: where users send BTC.
      - EURe (Gnosis) address: where users send EURe tokens.
      - A separate bridge system (outside this repo) watches those and
mints / burns the corresponding
        NEP‑141 tokens on NEAR.

  ———

  ## 4. How to start your own solver (step-by-step)

  This section turns the chart into a checklist.

  ### 4.1 Prerequisites

  - A machine or VPS (Linux) with:
      - Node.js 20+
      - npm or pnpm
  - A NEAR account dedicated to the solver, e.g. your-solver.near:
      - Never use your personal main wallet; create a new account just for
the solver.
      - Fund it with enough NEAR for gas + desired liquidity.
  - A full access private key for that solver account:
      - Export from NEAR CLI or wallet; format must be ed25519:....
      - This must be kept secret. Never commit it to git, never paste into
chat, never share it.
  - A relay auth key (RELAY_AUTH_KEY):
      - Provided by the relay / intents operator.
      - Usually a JWT-like token that identifies your solver.
  - Optionally:
      - A domain name + TLS (e.g. a subdomain like solver.example.com) if
you want a nice dashboard URL.
      - Nginx to proxy from HTTPS to the internal port.

  ### 4.2 Clone and install

  git clone https://github.com/near-intents/near-intents-examples.git
  cd near-intents-examples/near-intents-amm-solver

  # Using npm
  npm install

  (Replace repo URL with whichever remote you’re actually using.)

  ### 4.3 Create and fill your env file

  The solver looks for env in ./env/.env.<NODE_ENV>.

  For local/dev, we typically use NODE_ENV=local, so:

  cd near-intents-examples/near-intents-amm-solver
  mkdir -p env
  cp env/.env.example env/.env.local

  Open env/.env.local and set:

  Required core variables

  # Network
  NEAR_NETWORK_ID=mainnet

  # Tokens for this solver (example: EURe ↔ BTC)

AMM_TOKEN1_ID=nep141:gnosis-0x420ca0f9b9b604ce0fd9c18ef134c705e5fa3430.omft.near
  AMM_TOKEN2_ID=nep141:btc.omft.near

  # Non-TEE mode (simplest setup)
  TEE_ENABLED=false

  # Your solver NEAR account (dedicated!)
  NEAR_ACCOUNT_ID=your-solver.near
  NEAR_PRIVATE_KEY=ed25519:YOUR_SOLVER_PRIVATE_KEY_HERE

  Node / relay / margin

  # NEAR RPC – you can override; otherwise defaults are fine
  NEAR_NODE_URL=https://rpc.mainnet.near.org
  # or:
  # NEAR_NODE_URLS=https://free.rpc.fastnear.com,https://near.lava.build

  # Relay endpoint and auth
  RELAY_WS_URL=wss://solver-relay-v2.chaindefuser.com/ws
  RELAY_AUTH_KEY=YOUR_RELAY_AUTH_TOKEN

  # HTTP server port for the solver
  APP_PORT=3000          # or 4010 on your server

  # Logging and margin
  LOG_LEVEL=info         # error | warn | info | debug
  MARGIN_PERCENT=0.3     # 0.3% margin, adjust to your risk
  ONE_CLICK_API_ONLY=true

  Notes:

  - The Joi schema (src/configs/env.validation.ts) will enforce:
      - AMM_TOKEN1_ID, AMM_TOKEN2_ID are required.
      - Either TEE mode or NEAR_ACCOUNT_ID/NEAR_PRIVATE_KEY must be set
appropriately.
      - MARGIN_PERCENT must be positive.

  If the solver fails at startup with a validation error, it will list
which env variables are missing
  or invalid.

  ### 4.4 Run locally

  From the solver directory:

  # Make sure you're in near-intents-amm-solver
  NODE_ENV=local npm start

  You should see logs like:

  - Using Near RPC nodes: ...
  - Cron service started
  - WebSocket logs like Received intent: {...} once connected.

  Check:

  curl http://localhost:3000/status   # or your APP_PORT

  And open in browser:

  - http://localhost:3000/dashboard

  You should see the Solver Monitor dashboard.

  ### 4.5 Run in the background with pm2 (production-ish)

  On your server:

  cd /path/to/near-intents-examples/near-intents-amm-solver

  NODE_ENV=local pm2 start "npm start" --name near-solver
  pm2 save
  pm2 startup   # sets up pm2 to auto-start on boot

  Check logs:

  pm2 logs near-solver --lines 50

  Check HTTP:

  curl http://127.0.0.1:3000/status

  (Use your APP_PORT.)

  ### 4.6 Put it behind Nginx + TLS (optional but recommended)

  Basic Nginx server block (for a domain solver.example.com):

  server {
      listen 443 ssl http2;
      server_name solver.example.com;

      ssl_certificate     /etc/letsencrypt/live/
solver.example.com/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/
solver.example.com/privkey.pem;

      location / {
          proxy_pass http://127.0.0.1:3000;  # APP_PORT
          proxy_set_header Host $host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
      }
  }

  For your specific setup on emino.app, we instead:

  - Keep the existing blog at /.
  - Add:

  # Already configured in your vhost:
  location = /solver/ {
      proxy_pass http://127.0.0.1:4010/dashboard;
      ...
  }

  location /solver/ {
      proxy_pass http://127.0.0.1:4010/;
      ...
  }

  location /status {
      proxy_pass http://127.0.0.1:4010/status;
      ...
  }

  Then:

  nginx -t
  systemctl reload nginx

  Now your solver is reachable at:

  - https://yourdomain/solver/ – dashboard.
  - https://yourdomain/status – status JSON.

  ———

  ## 5. Security and operational notes

  - Keys:
      - Use a dedicated NEAR account for the solver.
      - The private key must have full access, or the solver can’t send txs.
      - Treat NEAR_PRIVATE_KEY and RELAY_AUTH_KEY as secrets:
          - Store in .env.local on the server.
          - Make sure the repo directory is not world-readable.
          - Never commit .env* files to git.
  - Funds:
      - Only keep as much liquidity/NEAR as you are willing to risk.
      - Withdraw profits periodically; think of the solver account as a
“hot wallet”.
  - Monitoring:
      - pm2 logs near-solver for runtime behavior.
      - curl /status for programmatic monitoring (you could plug this into
Prometheus / a health check).
  - Upgrades:
      - Pull new code, run npm install if dependencies changed.
      - Restart with pm2 restart near-solver.


https://mermaid.emino.app/?c=eJx1Vt1u6zYMfhXCwLk6-WmKYcNyMaAJip0ztFkXtygwpSgUW4m1Y0s-kuIkWHe7B9gj7klGSvJP0B0EsE3qI0V-JKX8mWQ6F8k82RteF3C33iiADx_gyQoDH0EoZ861lsqR3h62AUarpABYsIXRRxI3qnCutvPpVFRS6Qmv66nVZSPM9IWwQuUbdeHlNt8LtklWe6lOuNfjXQqss33ZJC9hixULiKbQ1uE2A8jQ7QLG45_eNsmnx8eHFNqtgT19fkGjVuu4O1hgv6S_rnCHN1gFY8w49QZQG50Jay8CDUsYqhLcjJEMpMWOeVWNwy7A6up6Dn41aPro77lUrMLHxFmMo9Q8v1UNOA1tBgA3dc1QCoijNAKQ0EZiHBHwCZll9EiDHmG1Ng6-u5pd4XdMawTTnNtiq7nJo-Fzyp7F1ursi3BLrZTInNSq92JEyc-AkNRDICsl5haNl0YrRo_BrsJIncsMjNgZYYuI_O2gHRIUXj365v4e-ZSZVHusLwUpWtc8KwTzzx4u1bgSlTZnhGrTQlfIKqNHD1zd3qxh_bAkp3KviG4P_Rwqw-J76NkrINPYzzxzUIiyjmZdA2EPkKFRvAQsAgZNWqofdRYViWR8eZGqMZSf06FErA3lwMwFgnIfKijFoRyT6GKjDoZdqY8kr2KzY7eezn2zY1fNrn-YXOFvNqfm6BuCihfBYQbeY8MCTUWbHL0vo-00fUadqs2gVWB8NGdINi9d4buN-lpgo34la3zHwoxgy0uusOFp90WX84JnX_ZGH1QOf-itH0piNjrHD7I3DS_JrI8ofEWUbzuwite20M5vELOJm6z9DHxsY-k47s-pU-gKPADaT7Bn60RluzH3Tlg8Q7xAo2zpOAzFGftRGzfXk8mktXlYsq6VFR7DNP47bh0dJCMoecNHYOpsQseHEu6yy5dtm3ddjda3T2tBlV08LqHWuowmKDJSRUeQi1pbSQazu4X8vQ-J7Jl3guT-rBBEMV2dZj9-v2xR3cAE4ojlUM4Bh3hznEQGhzpH8u1bnI7nNNYk6H1HZIh_jfZTiHJ04yl8zcK5JXJcL5GdV9Hg4qCOA8c7gTC_boct4aNFkgnUSHGEjJelbY-PHNwJY2zbt6V1MITLgX75fjqJ2pgYXZuRXQqfVkr59SBz6c4U0dCh5_n_7fzSNwzfdXguMpkLurl20vFtKaDnj-Po8AonKBAy3J7ybWcEaSA2qLQbZY8cr27hHHpCZoZ2yShxEvXtH4Y5XN7f3d0M__79D3zj3iYn55p80KhlBTcu-es_a-zoSA

![graph_browsernhttpseminoappsolver_nginx-_nginx-vhostneminoapp_2025-12-02T08-15-25](/media/how-to-start-your-own-near-solver-chart-technical-bits-env-k/graph_browsernhttpseminoappsolver_nginx-_nginx-vhostneminoapp_2025-12-02T08-15-25.svg)

![graph_browsernhttpseminoappsolver_nginx-_nginx-vhostneminoapp_2025-12-02T08-25-20](/media/how-to-start-your-own-near-solver-chart-technical-bits-env-k/graph_browsernhttpseminoappsolver_nginx-_nginx-vhostneminoapp_2025-12-02T08-25-20.svg)

---
*Post created via email from emin@nuri.com*
