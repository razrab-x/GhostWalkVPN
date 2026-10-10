import asyncio
import uuid
from datetime import datetime, timedelta

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, BufferedInputFile

from config import (
    BOT_TOKEN, ADMIN_IDS, VPN_NAME, PRICES,
    WG_SERVER_PUBLIC_KEY, WG_SERVER_ENDPOINT, WG_DNS,
)
import database as db
import wireguard as wg
import payments as pay
from keyboards import main_menu, plans_menu, pay_menu

bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

@dp.message(Command("start"))
async def cmd_start(m: Message):
    await db.add_user(m.from_user.id, m.from_user.username or "")
    await m.answer(
        f"👋 Привет, {m.from_user.first_name}!\n\n"
        f"Это <b>{VPN_NAME}</b> — быстрый WireGuard VPN.\n"
        f"Выбери действие:",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def cmd_admin(m: Message):
    if m.from_user.id not in ADMIN_IDS:
        return
    users, keys, total = await db.get_stats()
    await m.answer(
        f"📊 <b>Статистика {VPN_NAME}</b>\n\n"
        f"👥 Юзеров: <b>{users}</b>\n"
        f"🔑 Активных ключей: <b>{keys}</b>\n"
        f"💰 Заработано: <b>{total} ₽</b>"
    )

@dp.callback_query(F.data == "buy")
async def cb_buy(c: CallbackQuery):
    await c.message.edit_text("Выбери тариф:", reply_markup=plans_menu())
    await c.answer()

@dp.callback_query(F.data == "back")
async def cb_back(c: CallbackQuery):
    await c.message.edit_text("Главное меню:", reply_markup=main_menu())
    await c.answer()

@dp.callback_query(F.data.startswith("plan:"))
async def cb_plan(c: CallbackQuery):
    code = c.data.split(":")[1]
    plan = PRICES[code]
    order_id = f"gw_{c.from_user.id}_{uuid.uuid4().hex[:8]}"

    await db.create_payment(c.from_user.id, order_id, plan["amount"], code)

    result = await pay.create_payment(
        amount=plan["amount"],
        order_id=order_id,
        description=f"{VPN_NAME} {plan['label']}"
    )

    pay_url = result.get("pay_url") or result.get("url")
    if not pay_url:
        await c.message.edit_text(
            f"❌ Ошибка платежа:\n<code>{result}</code>",
            reply_markup=main_menu()
        )
        await c.answer()
        return

    await c.message.edit_text(
        f"📦 Тариф: <b>{plan['label']}</b>\n"
        f"💰 Сумма: <b>{plan['amount']} ₽</b>\n"
        f"🆔 Заказ: <code>{order_id}</code>\n\n"
        f"Нажми «Оплатить СБП» и отсканируй QR в банковском приложении.",
        reply_markup=pay_menu(order_id, pay_url)
    )
    await c.answer()

@dp.callback_query(F.data.startswith("check:"))
async def cb_check(c: CallbackQuery):
    order_id = c.data.split(":")[1]
    row = await db.get_payment_status(order_id)
    if row and row[0] == "paid":
        await c.message.edit_text(
            "✅ Платёж подтверждён. Ключ в разделе «Мои ключи».",
            reply_markup=main_menu()
        )
    else:
        await c.message.edit_text(
            "⏳ Платёж ещё не подтверждён. Подожди 1–2 минуты и нажми снова.",
            reply_markup=pay_menu(order_id, "#")
        )
    await c.answer()

@dp.callback_query(F.data == "my_keys")
async def cb_my_keys(c: CallbackQuery):
    keys = await db.get_user_keys(c.from_user.id)
    if not keys:
        await c.message.edit_text("У тебя пока нет ключей.", reply_markup=main_menu())
        await c.answer()
        return
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    for kid, addr, exp, active in keys:
        status = "🟢" if active else "🔴"
        rows.append([InlineKeyboardButton(
            text=f"{status} Ключ #{kid} · {addr} · до {str(exp)[:10]}",
            callback_data=f"getkey:{kid}"
        )])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="back")])
    await c.message.edit_text(
        "Твои ключи:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows)
    )
    await c.answer()

@dp.callback_query(F.data.startswith("getkey:"))
async def cb_getkey(c: CallbackQuery):
    kid = int(c.data.split(":")[1])
    row = await db.get_key_by_id(kid, c.from_user.id)
    if not row:
        await c.answer("Ключ не найден", show_alert=True)
        return
    priv, pub, addr, exp = row
    cfg = wg.build_client_config(priv, addr, WG_SERVER_PUBLIC_KEY, WG_SERVER_ENDPOINT, WG_DNS)
    file = BufferedInputFile(cfg.encode(), filename=f"ghostwalk_{addr}.conf")
    await c.message.answer_document(
        file,
        caption=f"🔑 Ключ #{kid}\nIP: <code>{addr}</code>\nДо: <code>{str(exp)[:10]}</code>"
    )
    await c.answer()

@dp.callback_query(F.data == "help")
async def cb_help(c: CallbackQuery):
    await c.message.edit_text(
        f"ℹ️ <b>Как подключиться к {VPN_NAME}:</b>\n\n"
        "1. Скачай <b>WireGuard</b> из App Store / Google Play.\n"
        "2. Получи .conf в разделе «Мои ключи».\n"
        "3. WireGuard → «+» → «Импорт из файла».\n"
        "4. Включи туннель.",
        reply_markup=main_menu()
    )
    await c.answer()

async def rolly_webhook(request: web.Request):
    body = await request.read()
    sig = request.headers.get("X-Signature", "")
    if not pay.verify_webhook(body, sig):
        return web.Response(status=403, text="bad signature")

    data = await request.json()
    order_id = data.get("order_id")
    status = data.get("status")

    if status == "paid" and order_id:
        row = await db.confirm_payment(order_id)
        if row:
            tg_id, plan_code = row
            plan = PRICES[plan_code]
            priv, pub = wg.gen_keypair()
            addr = wg.next_free_ip()
            wg.add_peer(pub, addr)
            expires = (datetime.utcnow() + timedelta(days=plan["days"])).isoformat()
            await db.add_vpn_key(tg_id, priv, pub, addr, expires)
            try:
                await bot.send_message(
                    tg_id,
                    f"✅ Оплата получена!\nТариф: <b>{plan['label']}</b>\n"
                    f"Ключ готов — забери в «Мои ключи»."
                )
            except Exception:
                pass
    return web.Response(text="ok")

async def start_webhook():
    app = web.Application()
    app.router.add_post("/webhook/rollypay", rolly_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

async def main():
    await db.init_db()
    await start_webhook()
    print(f"[{VPN_NAME}] Бот запущен, webhook на порту 8080")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
