# UZ KINO BOT — o‘rnatish qo‘llanmasi

Bu boshlang‘ich Telegram kino bot loyihasi. Unda kino qidirish, janrlar, sevimlilar, video yuborish va admin paneli bor.

## 1. Telegram bot ochish
1. Telegramda rasmiy `@BotFather` botini oching.
2. `/newbot` yuboring.
3. Bot nomi va username tanlang (username `bot` bilan tugashi kerak).
4. BotFather bergan tokenni hech kimga yubormang.

## 2. O‘rnatish
Python 3.10 yoki undan yangiroq versiya kerak.

Terminalda loyiha papkasiga kiring va bajaring:

```bash
python -m venv .venv
```

Windows:
```bash
.venv\Scripts\activate
```

macOS/Linux:
```bash
source .venv/bin/activate
```

Keyin:
```bash
pip install -r requirements.txt
```

`.env.example` faylidan nusxa olib `.env` deb nomlang. `BOT_TOKEN` o‘rniga BotFather tokenini, `ADMIN_IDS` o‘rniga o‘z Telegram raqamli ID’ingizni yozing.

Telegram ID’ni bilish uchun Telegramdagi ID ko‘rsatuvchi botdan foydalanishingiz mumkin; tokenni hech qachon ulashmang.

## 3. Botni ishga tushirish
```bash
python bot.py
```

Bot ishlayotgan kompyuter/server yoqilgan va internetga ulangan bo‘lishi kerak. Botni to‘xtatish uchun terminalda `Ctrl+C` bosing.

## 4. Kino qo‘shish
1. Botni Telegramda ochib `/start` yuboring.
2. `.env` ichida ko‘rsatilgan admin akkauntidan `/admin` yuboring.
3. **Kino qo‘shish** tugmasini bosing.
4. Kino nomi, yil, janr va tavsifni kiriting.
5. Videoni Telegramga video sifatida yuboring.
6. Bot videoning Telegram `file_id` qiymatini bazaga saqlaydi. Keyin shu faylni qayta yuklamasdan foydalanuvchiga yuborishi mumkin.

## 5. Muhim eslatmalar
- Hozircha SQLite bazasi lokal `kino.db` faylida saqlanadi. Uni o‘chirib yubormang; zaxira nusxa oling.
- Doimiy ishlashi uchun botni VPS yoki boshqa doimiy ishlaydigan serverga joylashtiring.
- Oddiy Telegram Bot API fayl hajmi va yuklash cheklovlariga ega. Katta videolar uchun Telegramning joriy cheklovlarini tekshiring yoki ruxsat etilgan hosting/streaming yechimini qo‘shing.
- Faqat o‘zingizga tegishli yoki tarqatish/namoyish qilish huquqingiz bor videolarni yuklang. Mualliflik huquqi bilan himoyalangan filmlarni ruxsatsiz tarqatmang.
- Bu MVP: hozircha kino afishasi, sahifalash, foydalanuvchi statistikasi va admin e’lonlari qo‘shilmagan.
