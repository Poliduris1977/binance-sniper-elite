# Crypto Sniper Elite v1.0

Quantitative research framework for detecting institutional accumulation on Binance Spot/Futures.

## Project Overview
This framework analyzes over 1.7 million candles across 500+ symbols to identify low-volatility compression patterns followed by volume breakouts.

### Key Performance Metrics:
- **Win Rate (Target Zone):** Up to 80% for break-even/small plus.
- **Explosive Growth (Zombies):** Identified 15+ "Golden Signals" with >15% gain.
- **Risk Control:** Integrated "Volume Trap" detection (prevents entry during distribution).

## Market Segmentation (Clusters)
1. **Mainstream:** Top-tier assets (BTC, ETH, SOL). High reliability, low frequency.
2. **Fresh Meat:** New listings (<30 days). High chaos, excluded from sniper strategy.
3. **Zombies:** Low-cap / Old assets. Primary hunting ground for 10x-50x RVOL breakouts.

## Quick Start
Run via Docker to ensure environment consistency:

`ash
# Update Market Database
docker run --rm -v ${PWD}:/app binance-research python3 src/fetch_data.py

# Run Sniper Scanner
docker run --rm -v ${PWD}:/app binance-research python3 src/sniper_core.py