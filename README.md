# OTC Signal Desk (signals only)

A mobile-friendly web dashboard for rule-based analysis of uploaded OHLC candles. It does not place trades.

## Included
- CALL / PUT / WAIT output
- ADX(14) threshold strictly greater than 27
- Requires a DI crossover and Vortex(14) crossover in the same direction on the latest closed candle
- 1-minute expiry label
- CSV upload with `open, high, low, close` headers (a `time` column is optional)
- Synthetic demo button clearly labeled as synthetic, never live data
- Render deployment files

## Important live-data limitation
This package does **not** include a live OTC market feed. Do not enter your API key into the webpage. To scan all available OTC markets automatically, the server must be integrated with your provider's documented API endpoints, authentication method, candle schema, and market-discovery endpoint. The API key alone is not enough to safely infer those details. Once you have the provider's API documentation, add the key as a private Render environment variable and implement the feed server-side.

## Deploy on Render using Android
1. Extract this ZIP.
2. Upload the folder to a GitHub repository (GitHub mobile website/app can do this, though uploading multiple files may be easier in a browser set to Desktop site).
3. In Render, create **New + → Web Service**, connect the repository.
4. Render detects `render.yaml`; if asked, use build command `pip install -r requirements.txt` and start command `gunicorn app:app`.
5. Deploy, then open the `onrender.com` URL on your Android phone.
6. For live integration later, use Render → service → Environment to add the provider key as a secret environment variable. Do not commit keys into GitHub or share them in chat.

## CSV example
`time,open,high,low,close`
`2026-10-27 00:01,1.2500,1.2510,1.2490,1.2505`

Use real, correctly timestamped one-minute candles and exclude the still-forming candle. Indicators are technical calculations, not predictions or guarantees.
