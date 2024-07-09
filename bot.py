import requests
import logging
import math
from telegram import Update, BotCommand, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, CallbackContext

# API token should ideally be stored securely
TOKEN = '7290813117:AAFk-2BJmWqFkcsvKedbai9aEnV5jigg3ik'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

PAGE_SIZE = 10

async def start(update: Update, context: CallbackContext) -> None:
    """Handler for /start command."""
    await update.message.reply_text('🌟 Chào mừng! Sử dụng /all_pools, /concentrated_pools, hoặc /standard_pools để xem thông tin về các liquidity pools trên Raydium. 🌟')

async def get_pools(endpoint, page):
    """Fetch pools data from Raydium API."""
    url = f'https://api-v3.raydium.io/{endpoint}&page={page}&pageSize={PAGE_SIZE}'
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for non-200 response
        data = response.json()
        logging.info(f"Fetched data: {data}")  # Log the fetched data
        return data.get('data', {}).get('data', [])  # Return the list of pools
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching {endpoint} pools: {e}")
        return []

async def get_total_pages(endpoint):
    """Fetch the total number of pages from Raydium API."""
    url = f'https://api-v3.raydium.io/{endpoint}&page=1&pageSize=1'  # Only fetching the first page to get the count
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise error for non-200 response
        data = response.json()
        logging.info(f"Total pages response data: {data}")  # Log the response data
        total_count = data.get('data', {}).get('count', 0)
        logging.info(f"Total count of items: {total_count}")  # Log the total count
        total_pages = max(1, math.ceil(total_count / PAGE_SIZE))  # Ensure total_pages is at least 1
        logging.info(f"Total pages: {total_pages}")  # Log the total pages
        return total_pages
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching total pages for {endpoint}: {e}")
        return 1

def format_pools(pools, pool_type, page, total_pages):
    """Format pools data into a readable message."""
    if not pools:
        return ["🚫 Không có thông tin pools để hiển thị."], None

    messages = []
    # of {total_pages} - 
    message = f"🔹 **Page {page} {pool_type.capitalize()} Liquidity Pools** 🔹\n\n"
    for pool in pools:
        tokenA = pool.get('mintA', {}).get('symbol', 'N/A')
        tokenB = pool.get('mintB', {}).get('symbol', 'N/A')
        pool_info = (
            f"🔸 **Token Pair:** {tokenA} ↔️ {tokenB}\n"
            f"💧 **Liquidity:** {pool.get('tvl', 'N/A')}\n"
            f"📈 **24h Volume:** {pool.get('day', {}).get('volume', 'N/A')}\n"
            f"💰 **24h Fee:** {pool.get('day', {}).get('volumeFee', 'N/A')}%\n"
            f"📊 **24h APR:** {pool.get('day', {}).get('apr', 'N/A')}%\n"
            f"🔗 [Add Liquidity to This Pool](https://raydium.io/liquidity/increase/?mode=add&pool_id={pool.get('id', '')})\n\n"
        )
        message += pool_info

    messages.append(message)
# of {total_pages}
    # Add navigation buttons
    keyboard = [
        [InlineKeyboardButton("Previous", callback_data=f'{pool_type}_pools_{page - 1}'),
         InlineKeyboardButton(f"Page {page} ", callback_data='noop'),
         InlineKeyboardButton("Next", callback_data=f'{pool_type}_pools_{page + 1}')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    return messages, reply_markup

async def all_pools(update: Update, context: CallbackContext) -> None:
    """Handler for /all_pools command."""
    page = 1
    endpoint = 'pools/info/list?poolType=all&poolSortField=default&sortType=desc'
    total_pages = await get_total_pages(endpoint)
    pools = await get_pools(endpoint, page)
    messages, reply_markup = format_pools(pools, "all", page, total_pages)
    for message in messages:
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def concentrated_pools(update: Update, context: CallbackContext) -> None:
    """Handler for /concentrated_pools command."""
    page = 1
    endpoint = 'pools/info/list?poolType=concentrated&poolSortField=default&sortType=desc'
    total_pages = await get_total_pages(endpoint)
    pools = await get_pools(endpoint, page)
    messages, reply_markup = format_pools(pools, "concentrated", page, total_pages)
    for message in messages:
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def standard_pools(update: Update, context: CallbackContext) -> None:
    """Handler for /standard_pools command."""
    page = 1
    endpoint = 'pools/info/list?poolType=standard&poolSortField=default&sortType=desc'
    total_pages = await get_total_pages(endpoint)
    pools = await get_pools(endpoint, page)
    messages, reply_markup = format_pools(pools, "standard", page, total_pages)
    for message in messages:
        await update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def handle_callback_query(update: Update, context: CallbackContext) -> None:
    """Handler for callback queries."""
    query = update.callback_query
    await query.answer()

    data = query.data
    pool_type, action, page = data.split('_')
    page = int(page)

    if page < 1:
        await query.message.reply_text("🚫 Đây là trang đầu tiên.")
        return

    endpoint = f'pools/info/list?poolType={pool_type}&poolSortField=default&sortType=desc'
    total_pages = await get_total_pages(endpoint)
    pools = await get_pools(endpoint, page)
    messages, reply_markup = format_pools(pools, pool_type, page, total_pages)
    for message in messages:
        await query.edit_message_text(text=message, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def error_handler(update: Update, context: CallbackContext) -> None:
    """Handle errors that occur during updates."""
    logging.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Set commands
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("all_pools", "View all available liquidity pools on Raydium"),
        BotCommand("concentrated_pools", "View all concentrated liquidity pools on Raydium"),
        BotCommand("standard_pools", "View all standard liquidity pools on Raydium")
    ]
    application.bot.set_my_commands(commands)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("all_pools", all_pools))
    application.add_handler(CommandHandler("concentrated_pools", concentrated_pools))
    application.add_handler(CommandHandler("standard_pools", standard_pools))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Register error handler
    application.add_error_handler(error_handler)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
