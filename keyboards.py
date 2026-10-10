from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import PRICES

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Купить VPN", callback_data="buy")],
        [InlineKeyboardButton(text="🔑 Мои ключи", callback_data="my_keys")],
        [InlineKeyboardButton(text="ℹ️ Помощь", callback_data="help")],
    ])

def plans_menu():
    rows = []
    for code, p in PRICES.items():
        rows.append([InlineKeyboardButton(
            text=f"{p['label']} — {p['amount']} ₽",
            callback_data=f"plan:{code}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

def pay_menu(order_id: str, pay_url: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 Оплатить СБП", url=pay_url)],
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"check:{order_id}")],
    ])
