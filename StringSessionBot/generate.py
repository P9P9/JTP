from asyncio.exceptions import TimeoutError
from Data import Data
from pyrogram import Client, filters
from telethon import TelegramClient
from telethon.sessions import StringSession
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import (
    ApiIdInvalid,
    PhoneNumberInvalid,
    PhoneCodeInvalid,
    PhoneCodeExpired,
    SessionPasswordNeeded,
    PasswordHashInvalid
)
from telethon.errors import (
    ApiIdInvalidError,
    PhoneNumberInvalidError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    SessionPasswordNeededError,
    PasswordHashInvalidError
)


@Client.on_message(filters.private & ~filters.forwarded & filters.command('generate'))
async def main(_, msg):
    await msg.reply(
        "اذا كنت تريد تنصيب جيبثون ميوزك فأختار بايروجرا, واذا تريد تنصيب التليثون فأختار تيرمكس",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("بايروجرام", callback_data="pyrogram"),
            InlineKeyboardButton("تيرمكس", callback_data="telethon")
        ]])
    )


async def generate_session(bot, msg, telethon=False):
    await msg.reply("Starting {} Session Generation...".format("Telethon" if telethon else "Pyrogram"))
    user_id = msg.chat.id
    api_id_msg = await bot.ask(user_id, '- أولا قم بأرسال الـ `API_ID`', filters=filters.text)
    if await cancelled(api_id_msg):
        return
    try:
        api_id = int(api_id_msg.text)
    except ValueError:
        await api_id_msg.reply('يوجد خطأ في الـ API_ID . قم بأعادة الخطوة من جديد.', quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    api_hash_msg = await bot.ask(user_id, 'حسنـا قم بأرسال الـ `API_HASH`', filters=filters.text)
    if await cancelled(api_id_msg):
        return
    api_hash = api_hash_msg.text
    phone_number_msg = await bot.ask(user_id, '- الان يرجى ارسال رقمك بشكل كامل , مثال :+964xxxxxxx', filters=filters.text)
    if await cancelled(api_id_msg):
        return
    phone_number = phone_number_msg.text
    await msg.reply("انتظر لحظة...")
    if telethon:
        client = TelegramClient(StringSession(), api_id, api_hash)
    else:
        client = Client(":memory:", api_id, api_hash)
    await client.connect()
    try:
        if telethon:
            code = await client.send_code_request(phone_number)
        else:
            code = await client.send_code(phone_number)
    except (ApiIdInvalid, ApiIdInvalidError):
        await msg.reply('`API_ID` و `API_HASH` ثنينهن خطأ. قم بأعادة الخطوة من جديد', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    except (PhoneNumberInvalid, PhoneNumberInvalidError):
        await msg.reply('`PHONE_NUMBER` خطأ. رجاءا قم بأعادة الاستخراج من جديد.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    try:
        phone_code_msg = await bot.ask(user_id, "يرجى التحقق من وجود كلمة مرور في حسابك. إذا كان هناك تحقق بخطوتين( المرور ) ، أرسل كلمة المرور هنا بعد ارسال كود الدخول بالتنسيق أدناه.- اذا كانت كلمة المرور او الكود  هي 12345 يرجى ارسالها بالشكل التالي 1 2 3 4 5 مع وجود مسـافـات بين الارقام اذا احتجت مساعدة @jepthon", filters=filters.text, timeout=600)
        if await cancelled(api_id_msg):
            return
    except TimeoutError:
        await msg.reply('لقد بلغ الحد الزمني 10 دقايق. ارجع عيد الخطوات من جديد.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    phone_code = phone_code_msg.text.replace(" ", "")
    try:
        if telethon:
            await client.sign_in(phone_number, phone_code, password=None)
        else:
            await client.sign_in(phone_number, code.phone_code_hash, phone_code)
    except (PhoneCodeInvalid, PhoneCodeInvalidError):
        await msg.reply('الكود خطأ. ارجع عيد من جديد.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    except (PhoneCodeExpired, PhoneCodeExpiredError):
        await msg.reply('الكود انتهت صلاحيته. ارجع عيد من جديد.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return
    except (SessionPasswordNeeded, SessionPasswordNeededError):
        try:
            two_step_msg = await bot.ask(user_id, 'حسابك يحتوي على التحقق بخطوتين - قم بكتابة الرمز لاتخاف حسابك آمن لدى جيبثون .', filters=filters.text, timeout=300)
        except TimeoutError:
            await msg.reply('لغد بلغ الحد الزمني 5 دقايق. ارجع عيد من جديد.', reply_markup=InlineKeyboardMarkup(Data.generate_button))
            return
        try:
            password = two_step_msg.text
            if telethon:
                await client.sign_in(password=password)
            else:
                await client.check_password(password=password)
            if await cancelled(api_id_msg):
                return
        except (PasswordHashInvalid, PasswordHashInvalidError):
            await two_step_msg.reply('الباسورد خطأ. قم بأعادة الخطوة من جديد.', quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
            return
    if telethon:
        string_session = client.session.save()
    else:
        string_session = await client.export_session_string()
    text = "**{} STRING SESSION** \n\n`{}` \n\nمن قبل  @jepthon".format("TELETHON" if telethon else "PYROGRAM", string_session)
    try:
        await client.send_message("me", text)
    except KeyError:
        pass
    await client.disconnect()
    await phone_code_msg.reply("تم أستخراج بنجاح {} string session. \n\nاذهب الى الرسائل المحفوظة! \n\nتم ألاستخراج من قبل @jepthon".format("telethon" if telethon else "pyrogram"))


async def cancelled(msg):
    if "/cancel" in msg.text:
        await msg.reply("تم الغاء الاستخراج!", quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return True
    elif "/restart" in msg.text:
        await msg.reply("تم ترسيت البوت !", quote=True, reply_markup=InlineKeyboardMarkup(Data.generate_button))
        return True
    elif msg.text.startswith("/"):  # Bot Commands
        await msg.reply("تم ألغاء الاستخراج!", quote=True)
        return True
    else:
        return False
