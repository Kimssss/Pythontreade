#!/bin/bash
# Demo mode environment variables setup

echo "Setting up demo environment..."

# Demo credentials (these should be your actual demo API credentials)
export TRADING_MODE=demo
export KIS_DEMO_APPKEY="PSJyUgEGfMBUjVuoNQDzqJyBMoJJfBKAZBpD"
export KIS_DEMO_APPSECRET="q0IY3hqPGBJ7K8r+fDZpZvCm8u2cTZNy7L0WmhJJi7I5RQPLr9AeGl6Pl6TFYUcdONDgtvD0KOyi5N/LIxJCLz/sL5c7b4RXOGPgm5c0k0FqeBqk3VLKUOIazK9w6HCvqRUGUBxtnKRiKcozh5hSC1KTFS5z+HjdU1bGlcPYLRs="
export KIS_DEMO_ACCOUNT="50114632-01"

# Global trading mode
export GLOBAL_TRADING_MODE="both"  # domestic, overseas, both

echo "Demo environment variables set!"
echo "TRADING_MODE: $TRADING_MODE"
echo "Account: $KIS_DEMO_ACCOUNT"