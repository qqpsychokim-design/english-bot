import asyncio
import os
import random
import re
import json
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# ==================== ЗАГРУЗКА СЛОВ ====================
def load_words():
    words = []
    try:
        with open("words.txt", "r", encoding="utf-8") as f:
            for line in f:
                if "," in line:
                    parts = line.strip().split(",")
                    words.append({"ru": parts[0], "en": parts[1]})
    except:
        words = [{"ru": "кот", "en": "cat"}, {"ru": "собака", "en": "dog"}]
    return words

all_words = load_words()
print(f"✅ Загружено {len(all_words)} слов")

# ==================== RPG СИСТЕМА ====================
PROFILES_FILE = "profiles.json"

LEVELS = [
    {"level": 1, "name": "🌱 Новичок", "xp": 0},
    {"level": 2, "name": "📖 Ученик", "xp": 100},
    {"level": 3, "name": "✏️ Знаток", "xp": 300},
    {"level": 4, "name": "🗣️ Разговорник", "xp": 600},
    {"level": 5, "name": "⭐ Продвинутый", "xp": 1000},
    {"level": 6, "name": "🏆 Мастер", "xp": 1500},
    {"level": 7, "name": "👑 Эксперт", "xp": 2100},
    {"level": 8, "name": "💎 Профи", "xp": 2800},
    {"level": 9, "name": "🔥 Гуру", "xp": 3600},
    {"level": 10, "name": "🎓 Легенда", "xp": 5000},
]

def get_profile(user_id):
    if os.path.exists(PROFILES_FILE):
        with open(PROFILES_FILE, "r") as f:
            profiles = json.load(f)
    else:
        profiles = {}
    uid = str(user_id)
    if uid not in profiles:
        profiles[uid] = {"xp": 0, "correct": 0, "wrong": 0, "games": 0}
    return profiles, profiles[uid]

def save_profile(profiles):
    with open(PROFILES_FILE, "w") as f:
        json.dump(profiles, f, indent=2)

def update_xp(user_id, delta):
    profiles, profile = get_profile(user_id)
    profile["xp"] = max(0, profile["xp"] + delta)
    if delta > 0:
        profile["correct"] += 1
    else:
        profile["wrong"] += 1
    save_profile(profiles)
    return profile["xp"]

def get_level(xp):
    for i in range(len(LEVELS)-1, -1, -1):
        if xp >= LEVELS[i]["xp"]:
            return LEVELS[i]["level"], LEVELS[i]["name"]
    return 1, "🌱 Новичок"

# ==================== ТЕМЫ ====================
topics = [
    {"q": "What did you eat for breakfast?", "kw": ["eat","ate","breakfast","food"], "ru": "Что ел на завтрак?"},
    {"q": "What is your hobby?", "kw": ["hobby","like","play","read"], "ru": "Твоё хобби?"},
    {"q": "Where would you like to travel?", "kw": ["travel","go","visit","country"], "ru": "Куда хочешь поехать?"},
]

easy_q = [
    {"q": "What is your name?", "ru": "Как тебя зовут?"},
    {"q": "How old are you?", "ru": "Сколько лет?"},
]

hard_q = [
    {"q": "What would you do with a million dollars?", "ru": "Что бы сделал с миллионом?"},
]

sentences = [
    {"en": "Hello, how are you?", "ru": ["привет как дела", "здравствуй как ты"]},
    {"en": "I like to read books.", "ru": ["я люблю читать книги", "мне нравится читать книги"]},
]

# ==================== КНОПКИ ====================
main_keyboard = ReplyKeyboardMarkup([
    ["🇬🇧 Обычный", "🎮 Игра слов"],
    ["📖 Игра перевод", "📝 Тест слов"],
    ["👤 Профиль", "📚 Справочник", "ℹ️ Инфо"]
], resize_keyboard=True)

# ==================== СОСТОЯНИЯ ПОЛЬЗОВАТЕЛЕЙ ====================
user_state = {}

def check_grammar(txt):
    errors = []
    t = txt.lower()
    if len(t) < 2:
        errors.append("❌ Ничего не написал")
    if txt and txt[0].islower():
        errors.append("📌 Начинай с заглавной")
    if "i am like" in t:
        errors.append("❌ 'I am like' → 'I like'")
    return errors

def check_translate(user_txt, variants):
    user_txt = user_txt.lower().strip()
    for v in variants:
        if user_txt == v.lower() or v.lower() in user_txt:
            return True
    return False

# ==================== КОМАНДЫ ====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    t = random.choice(topics)
    user_state[uid] = {"mode": "normal", "topic": t}
    await update.message.reply_text(
        f"🤖 *English Bot*\n\n*Первый вопрос:*\n{t['q']}\n\n_(перевод: {t['ru']})_",
        parse_mode="Markdown",
        reply_markup=main_keyboard
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    profiles, profile = get_profile(uid)
    xp = profile["xp"]
    lvl, lvl_name = get_level(xp)
    correct = profile["correct"]
    wrong = profile["wrong"]
    total = correct + wrong
    accuracy = int(correct/total*100) if total > 0 else 0
    await update.message.reply_text(
        f"👤 *ПРОФИЛЬ*\n\n🏆 {lvl_name} (ур. {lvl})\n⭐ Опыт: {xp}\n✅ Правильно: {correct}\n❌ Неправильно: {wrong}\n🎯 Точность: {accuracy}%",
        parse_mode="Markdown"
    )

async def wordgame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    words = random.sample(all_words, min(10, len(all_words)))
    user_state[uid] = {"mode": "word_game", "words": words, "idx": 0, "score": 0, "dir": random.choice([0,1])}
    w = words[0]
    if user_state[uid]["dir"] == 0:
        await update.message.reply_text(f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇷🇺 {w['ru']} → ?", parse_mode="Markdown")
    else:
        await update.message.reply_text(f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇬🇧 {w['en']} → ?", parse_mode="Markdown")

async def translategame(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    sents = random.sample(sentences, min(5, len(sentences)))
    user_state[uid] = {"mode": "translate_game", "sents": sents, "idx": 0, "score": 0}
    s = sents[0]
    await update.message.reply_text(f"📖 *Игра перевод* (+15XP/-5XP)\n\n1/5: 🇬🇧 {s['en']}\n\n✏️ Напиши перевод:", parse_mode="Markdown")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    profiles, profile = get_profile(uid)
    xp = profile["xp"]
    lvl, lvl_name = get_level(xp)
    await update.message.reply_text(
        f"📋 *ИНФО*\n\n"
        f"*Команды:* /start, /profile, /wordgame, /translategame\n\n"
        f"*Твой уровень:* {lvl_name} (ур. {lvl})\n"
        f"*Опыт:* {xp}\n\n"
        f"*За что XP:*\n🎮 Игра слов: +10/-5\n📖 Игра перевод: +15/-5",
        parse_mode="Markdown"
    )

async def materials(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 *СПРАВОЧНИК*\n\n"
        "/start - начать\n"
        "/profile - статистика\n"
        "/wordgame - игра слов\n"
        "/translategame - игра перевод\n"
        "/info - информация",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    answer = update.message.text.strip()
    
    if uid not in user_state:
        await update.message.reply_text("Нажми /start")
        return
    
    mode = user_state[uid].get("mode")
    
    # ИГРА СЛОВ
    if mode == "word_game":
        data = user_state[uid]
        idx = data["idx"]
        words = data["words"]
        if idx >= len(words):
            xp_gain = data["score"] * 10
            update_xp(uid, xp_gain)
            await update.message.reply_text(f"🎉 Игра окончена! Очки: {data['score']}/10\n+{xp_gain} XP!")
            del user_state[uid]
            return
        w = words[idx]
        if data["dir"] == 0:
            correct = answer.lower().strip() == w["en"].lower()
        else:
            correct = answer.lower().strip() == w["ru"].lower()
        if correct:
            data["score"] += 1
            update_xp(uid, 10)
            await update.message.reply_text(f"✅ +10 XP! ({data['score']}/10)")
        else:
            update_xp(uid, -5)
            if data["dir"] == 0:
                await update.message.reply_text(f"❌ -5 XP! {w['ru']} → {w['en']}")
            else:
                await update.message.reply_text(f"❌ -5 XP! {w['en']} → {w['ru']}")
        data["idx"] += 1
        if data["idx"] < len(words):
            nw = words[data["idx"]]
            num = data["idx"] + 1
            if data["dir"] == 0:
                await update.message.reply_text(f"Слово {num}/10: 🇷🇺 {nw['ru']} → ?")
            else:
                await update.message.reply_text(f"Слово {num}/10: 🇬🇧 {nw['en']} → ?")
        else:
            xp_gain = data["score"] * 10
            update_xp(uid, xp_gain)
            await update.message.reply_text(f"🎉 Игра окончена! {data['score']}/10\n+{xp_gain} XP!")
            del user_state[uid]
        return
    
    # ИГРА ПЕРЕВОД
    if mode == "translate_game":
        data = user_state[uid]
        idx = data["idx"]
        sents = data["sents"]
        if idx >= len(sents):
            xp_gain = data["score"] * 15
            update_xp(uid, xp_gain)
            await update.message.reply_text(f"🎉 Игра окончена! Очки: {data['score']}/5\n+{xp_gain} XP!")
            del user_state[uid]
            return
        s = sents[idx]
        if check_translate(answer, s["ru"]):
            data["score"] += 1
            update_xp(uid, 15)
            await update.message.reply_text(f"✅ +15 XP! ({data['score']}/5)")
        else:
            update_xp(uid, -5)
            await update.message.reply_text(f"❌ -5 XP! Правильно: {s['ru'][0]}")
        data["idx"] += 1
        if data["idx"] < len(sents):
            ns = sents[data["idx"]]
            num = data["idx"] + 1
            await update.message.reply_text(f"Предложение {num}/5: 🇬🇧 {ns['en']}\n\n✏️ Перевод:")
        else:
            xp_gain = data["score"] * 15
            update_xp(uid, xp_gain)
            await update.message.reply_text(f"🎉 Игра окончена! {data['score']}/5\n+{xp_gain} XP!")
            del user_state[uid]
        return
    
    # ОБЫЧНЫЙ РЕЖИМ
    if mode == "normal":
        topic = user_state[uid].get("topic")
        if not topic:
            await update.message.reply_text("Ошибка, нажми /start")
            return
        errors = check_grammar(answer)
        response = f"📝 *{answer}*\n\n"
        if errors:
            response += "\n".join(errors)
        else:
            response += "✅ Грамматика верна"
        await update.message.reply_text(response, parse_mode="Markdown")
        new_t = random.choice(topics)
        user_state[uid]["topic"] = new_t
        await update.message.reply_text(f"🔹 *Следующий вопрос:*\n{new_t['q']}\n\n_(перевод: {new_t['ru']})_", parse_mode="Markdown")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "🇬🇧 Обычный":
        uid = update.effective_user.id
        t = random.choice(topics)
        user_state[uid] = {"mode": "normal", "topic": t}
        await update.message.reply_text(f"*Вопрос:*\n{t['q']}\n\n_(перевод: {t['ru']})_", parse_mode="Markdown")
    elif text == "🎮 Игра слов":
        await wordgame(update, context)
    elif text == "📖 Игра перевод":
        await translategame(update, context)
    elif text == "👤 Профиль":
        await profile(update, context)
    elif text == "📚 Справочник":
        await materials(update, context)
    elif text == "ℹ️ Инфо":
        await info(update, context)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profile", profile))
    app.add_handler(CommandHandler("wordgame", wordgame))
    app.add_handler(CommandHandler("translategame", translategame))
    app.add_handler(CommandHandler("materials", materials))
    app.add_handler(CommandHandler("info", info))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.TEXT & filters.Regex("^(🇬🇧 Обычный|🎮 Игра слов|📖 Игра перевод|👤 Профиль|📚 Справочник|ℹ️ Инфо)$"), button_handler))
    print(f"✅ Бот запущен! {len(all_words)} слов")
    app.run_polling()

if __name__ == "__main__":
    main()
