import os
import logging
import asyncio
import sqlite3
from contextlib import closing

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardMarkup, KeyboardButton
)
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_IDS = {
    int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",")
    if x.strip().isdigit()
}
DB_PATH = os.getenv("DB_PATH", "kino.db")

logging.basicConfig(level=logging.INFO)
bot = Bot(BOT_TOKEN)
dp = Dispatcher()

GENRES = ["Komediya", "Jangari", "Drama", "Fantastika", "Sarguzasht", "Multfilm", "Oilaviy", "Boshqa"]

def db():
    return sqlite3.connect(DB_PATH)

def init_db():
    with closing(db()) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS movies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                year TEXT DEFAULT '',
                genre TEXT NOT NULL,
                description TEXT DEFAULT '',
                file_id TEXT NOT NULL,
                added_by INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        con.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                user_id INTEGER NOT NULL,
                movie_id INTEGER NOT NULL,
                UNIQUE(user_id, movie_id)
            )
        """)
        con.commit()

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔎 Kino qidirish"), KeyboardButton(text="🎭 Janrlar")],
            [KeyboardButton(text="⭐ Sevimlilar"), KeyboardButton(text="ℹ️ Yordam")],
        ],
        resize_keyboard=True
    )

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Kino qo‘shish", callback_data="admin:add")],
        [InlineKeyboardButton(text="🗑 Kino o‘chirish", callback_data="admin:delete")],
        [InlineKeyboardButton(text="📊 Statistika", callback_data="admin:stats")],
    ])

def movie_keyboard(movie_id, user_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Kinoni yuborish", callback_data=f"movie:watch:{movie_id}")],
        [InlineKeyboardButton(text="⭐ Sevimlilarga qo‘shish", callback_data=f"movie:favorite:{movie_id}")],
    ])

def get_movie(movie_id):
    with closing(db()) as con:
        return con.execute(
            "SELECT id,title,year,genre,description,file_id FROM movies WHERE id=?",
            (movie_id,)
        ).fetchone()

def movie_caption(row):
    _, title, year, genre, description, _ = row
    caption = f"🎬 <b>{title}</b>"
    if year:
        caption += f" ({year})"
    caption += f"\n🎭 Janr: {genre}"
    if description:
        caption += f"\n\n{description}"
    return caption

class AddMovie(StatesGroup):
    title = State()
    year = State()
    genre = State()
    description = State()
    video = State()

class DeleteMovie(StatesGroup):
    movie_id = State()

class SearchMovie(StatesGroup):
    query = State()

@dp.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🎬 <b>UZ KINO BOT</b>ga xush kelibsiz!\n\n"
        "O‘zbekcha tarjimada ruxsat bilan joylangan kinolarni qidiring va tomosha qiling.",
        reply_markup=main_menu()
    )

@dp.message(Command("admin"))
async def admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Bu buyruq faqat adminlar uchun.")
        return
    await message.answer("🛠 Admin paneli", reply_markup=admin_menu())

@dp.callback_query(F.data == "admin:add")
async def admin_add(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.set_state(AddMovie.title)
    await call.message.answer("Kino nomini yuboring:")
    await call.answer()

@dp.message(AddMovie.title)
async def add_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await state.set_state(AddMovie.year)
    await message.answer("Chiqqan yilini yozing (noma’lum bo‘lsa — belgisi yuboring):")

@dp.message(AddMovie.year)
async def add_year(message: Message, state: FSMContext):
    await state.update_data(year="" if message.text.strip() == "—" else message.text.strip())
    await state.set_state(AddMovie.genre)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"genre:{g}")] for g in GENRES
    ])
    await message.answer("Janrni tanlang:", reply_markup=kb)

@dp.callback_query(AddMovie.genre, F.data.startswith("genre:"))
async def add_genre(call: CallbackQuery, state: FSMContext):
    await state.update_data(genre=call.data.split(":", 1)[1])
    await state.set_state(AddMovie.description)
    await call.message.answer("Qisqa tavsif yuboring (tavsif bo‘lmasa — yozing: yo‘q)")
    await call.answer()

@dp.message(AddMovie.description)
async def add_description(message: Message, state: FSMContext):
    desc = "" if message.text.strip().lower() == "yo‘q" else message.text.strip()
    await state.update_data(description=desc)
    await state.set_state(AddMovie.video)
    await message.answer("Endi kinoning video faylini yuboring. Video Telegramda ochilishi uchun uni video sifatida yuboring.")

@dp.message(AddMovie.video, F.video)
async def add_video(message: Message, state: FSMContext):
    data = await state.get_data()
    with closing(db()) as con:
        cur = con.execute(
            "INSERT INTO movies(title,year,genre,description,file_id,added_by) VALUES(?,?,?,?,?,?)",
            (data["title"], data["year"], data["genre"], data["description"],
             message.video.file_id, message.from_user.id)
        )
        movie_id = cur.lastrowid
        con.commit()
    await state.clear()
    await message.answer(f"✅ Kino qo‘shildi! ID: <code>{movie_id}</code>", reply_markup=main_menu())

@dp.message(AddMovie.video)
async def wrong_video(message: Message):
    await message.answer("Iltimos, kinoni Telegram video fayli sifatida yuboring. Boshqa xabar qabul qilinmadi.")

@dp.callback_query(F.data == "admin:delete")
async def admin_delete(call: CallbackQuery, state: FSMContext):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    await state.set_state(DeleteMovie.movie_id)
    await call.message.answer("O‘chirmoqchi bo‘lgan kino ID raqamini yuboring:")
    await call.answer()

@dp.message(DeleteMovie.movie_id)
async def delete_movie(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await state.clear()
        return
    try:
        movie_id = int(message.text.strip())
    except ValueError:
        await message.answer("ID raqami son bo‘lishi kerak. Qayta yuboring:")
        return
    with closing(db()) as con:
        cur = con.execute("DELETE FROM movies WHERE id=?", (movie_id,))
        con.execute("DELETE FROM favorites WHERE movie_id=?", (movie_id,))
        con.commit()
    await state.clear()
    await message.answer("✅ Kino o‘chirildi." if cur.rowcount else "Bunday ID topilmadi.", reply_markup=main_menu())

@dp.callback_query(F.data == "admin:stats")
async def admin_stats(call: CallbackQuery):
    if call.from_user.id not in ADMIN_IDS:
        await call.answer("Ruxsat yo‘q", show_alert=True)
        return
    with closing(db()) as con:
        count = con.execute("SELECT COUNT(*) FROM movies").fetchone()[0]
        genres = con.execute("SELECT genre, COUNT(*) FROM movies GROUP BY genre ORDER BY COUNT(*) DESC").fetchall()
    text = f"📊 <b>Statistika</b>\nKinolar soni: {count}"
    if genres:
        text += "\n\n" + "\n".join(f"• {g}: {n}" for g, n in genres)
    await call.message.answer(text)
    await call.answer()

@dp.message(F.text == "🔎 Kino qidirish")
async def search_prompt(message: Message, state: FSMContext):
    await state.set_state(SearchMovie.query)
    await message.answer("Kino nomini yoki nomining bir qismini yozing:")

@dp.message(SearchMovie.query)
async def search_results(message: Message, state: FSMContext):
    query = message.text.strip()
    await state.clear()
    with closing(db()) as con:
        rows = con.execute(
            "SELECT id,title,year,genre,description,file_id FROM movies WHERE title LIKE ? ORDER BY title LIMIT 15",
            (f"%{query}%",)
        ).fetchall()
    if not rows:
        await message.answer("😕 Bu nom bo‘yicha kino topilmadi. Boshqa nom bilan urinib ko‘ring.", reply_markup=main_menu())
        return
    await message.answer(f"🔎 Natijalar: {len(rows)} ta")
    for row in rows:
        await message.answer(movie_caption(row), reply_markup=movie_keyboard(row[0], message.from_user.id), parse_mode="HTML")

@dp.message(F.text == "🎭 Janrlar")
async def show_genres(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=g, callback_data=f"browse:{g}")] for g in GENRES
    ])
    await message.answer("Janrni tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith("browse:"))
async def browse_genre(call: CallbackQuery):
    genre = call.data.split(":", 1)[1]
    with closing(db()) as con:
        rows = con.execute(
            "SELECT id,title,year,genre,description,file_id FROM movies WHERE genre=? ORDER BY title LIMIT 20",
            (genre,)
        ).fetchall()
    if not rows:
        await call.message.answer(f"Bu janrda hozircha kino yo‘q: {genre}")
    else:
        await call.message.answer(f"🎭 {genre} janridagi kinolar:")
        for row in rows:
            await call.message.answer(movie_caption(row), reply_markup=movie_keyboard(row[0], call.from_user.id), parse_mode="HTML")
    await call.answer()

@dp.callback_query(F.data.startswith("movie:watch:"))
async def watch_movie(call: CallbackQuery):
    try:
        movie_id = int(call.data.rsplit(":", 1)[1])
    except ValueError:
        await call.answer("Kino ID xato", show_alert=True)
        return
    row = get_movie(movie_id)
    if not row:
        await call.answer("Kino topilmadi", show_alert=True)
        return
    await call.message.answer_video(
        video=row[5],
        caption=movie_caption(row),
        parse_mode="HTML"
    )
    await call.answer()

@dp.callback_query(F.data.startswith("movie:favorite:"))
async def favorite_movie(call: CallbackQuery):
    movie_id = int(call.data.rsplit(":", 1)[1])
    with closing(db()) as con:
        try:
            con.execute("INSERT INTO favorites(user_id,movie_id) VALUES(?,?)", (call.from_user.id, movie_id))
            con.commit()
            result = "⭐ Sevimlilarga qo‘shildi!"
        except sqlite3.IntegrityError:
            result = "Bu kino sevimlilaringizda bor."
    await call.answer(result, show_alert=True)

@dp.message(F.text == "⭐ Sevimlilar")
async def favorites(message: Message):
    with closing(db()) as con:
        rows = con.execute("""
            SELECT m.id,m.title,m.year,m.genre,m.description,m.file_id
            FROM movies m JOIN favorites f ON m.id=f.movie_id
            WHERE f.user_id=? ORDER BY m.title
        """, (message.from_user.id,)).fetchall()
    if not rows:
        await message.answer("Hozircha sevimlilar ro‘yxatingiz bo‘sh.")
        return
    for row in rows:
        await message.answer(movie_caption(row), reply_markup=movie_keyboard(row[0], message.from_user.id), parse_mode="HTML")

@dp.message(F.text == "ℹ️ Yordam")
async def help_message(message: Message):
    await message.answer(
        "🔎 Kino qidirish — kino nomini yozing.\n"
        "🎭 Janrlar — kerakli janrni tanlang.\n"
        "⭐ Sevimlilar — saqlangan kinolaringiz.\n\n"
        "Adminlar /admin buyrug‘i orqali boshqaruv panelini ochadi.",
        reply_markup=main_menu()
    )

async def main():
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN .env faylida ko‘rsatilmagan.")
    init_db()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
