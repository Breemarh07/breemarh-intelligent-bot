import os
import requests
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

BOT_NAME = "Breemarh Intelligent Bot"


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    message = (
        f"Welcome to {BOT_NAME}! 🚀\n\n"
        "Your Solana research assistant.\n\n"
        "Commands:\n"
        "/start - Show this message\n"
        "/analyze <contract_address> - Inspect a token\n"
    )

    await update.message.reply_text(message)


async def analyze(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not context.args:
        await update.message.reply_text(
            "Usage:\n/analyze <Solana_contract_address>"
        )
        return

    contract = context.args[0].strip()

    await update.message.reply_text(
        "🔎 Checking token market data..."
    )

    try:
        url = (
            "https://api.dexscreener.com/latest/dex/tokens/"
            + contract
        )

        response = requests.get(url, timeout=20)
        response.raise_for_status()
        data = response.json()

        pairs = data.get("pairs") or []

        solana_pairs = [
            pair for pair in pairs
            if pair.get("chainId") == "solana"
        ]

        if not solana_pairs:
            await update.message.reply_text(
                "No Solana market pairs found for this address."
            )
            return

        pair = max(
            solana_pairs,
            key=lambda p: (p.get("liquidity") or {}).get("usd", 0),
        )

        liquidity = (pair.get("liquidity") or {}).get("usd", 0)
        volume = (pair.get("volume") or {}).get("h24", 0)
        ratio = volume / liquidity if liquidity > 0 else None

        ratio_text = (
            f"{ratio:.2f}x" if ratio is not None
            else "Unavailable (zero or missing liquidity)"
        )

        message = (
            "📊 TOKEN MARKET REPORT\n\n"
            f"Name: {pair.get('baseToken', {}).get('name', 'Unknown')}\n"
            f"Symbol: {pair.get('baseToken', {}).get('symbol', 'Unknown')}\n"
            f"Price: ${pair.get('priceUsd', 'Unknown')}\n"
            f"Liquidity: ${liquidity:,.2f}\n"
            f"24h Volume: ${volume:,.2f}\n"
            f"Volume/Liquidity: {ratio_text}\n"
            f"Chart: {pair.get('url', 'Unavailable')}\n\n"
            "⚠️ Preliminary market-data check only.\n"
            "Token age, historical drawdown, 4H reversal, "
            "holder quality, and retest are not yet verified."
        )

        await update.message.reply_text(message)

    except requests.RequestException:
        await update.message.reply_text(
            "Market-data request failed. Please try again later."
        )
    except Exception:
        await update.message.reply_text(
            "An unexpected error occurred while analysing this token."
        )


def main():
    token = os.getenv("TELEGRAM_BOT_TOKEN")

    if not token:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN environment variable."
        )

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("analyze", analyze))

    print(f"{BOT_NAME} is starting...")
    app.run_polling()


if __name__ == "__main__":
    main()
