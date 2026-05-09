import asyncio
import os
import random
import re
import json
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from dotenv import load_dotenv

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ==================== МЕНЮ ====================
main_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🇬🇧 Обычный"), KeyboardButton(text="🎮 Игра слов")],
        [KeyboardButton(text="📖 Игра перевод"), KeyboardButton(text="📝 Тест слов")],
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🔄 Следующий")],
        [KeyboardButton(text="📚 Справочник"), KeyboardButton(text="ℹ️ Инфо")]
    ],
    resize_keyboard=True
)

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
    {"q": "Describe your best friend.", "kw": ["friend","kind","funny","smart"], "ru": "Опиши друга."},
    {"q": "What do you want to be?", "kw": ["future","want","be","doctor"], "ru": "Кем хочешь стать?"},
    {"q": "What kind of movies do you like?", "kw": ["movie","film","like","comedy"], "ru": "Любимые фильмы?"},
]

easy_q = [
    {"q": "What is your name?", "ru": "Как тебя зовут?"},
    {"q": "How old are you?", "ru": "Сколько лет?"},
    {"q": "Where are you from?", "ru": "Откуда ты?"},
]

hard_q = [
    {"q": "What would you do with a million dollars?", "ru": "Что бы сделал с миллионом?"},
    {"q": "What is the most important lesson life taught you?", "ru": "Главный урок жизни?"},
]

sentences = [
    {"en": "Hello, how are you?", "ru": ["привет как дела", "здравствуй как ты"]},
    {"en": "I like to read books.", "ru": ["я люблю читать книги", "мне нравится читать книги"]},
    {"en": "What time is it?", "ru": ["сколько времени", "который час"]},
    {"en": "Where do you live?", "ru": ["где ты живешь", "где вы живете"]},
    {"en": "I am happy today.", "ru": ["я счастлив сегодня", "я рад сегодня"]},
]

def check_grammar(txt):
    errors = []
    t = txt.lower()
    if len(t) < 2:
        errors.append("❌ Ничего не написал")
    if re.search(r'[а-яё]', t):
        errors.append("❌ Русские буквы")
    if txt and txt[0].islower():
        errors.append("📌 Начинай с заглавной")
    if "i am like" in t:
        errors.append("❌ 'I am like' → 'I like'")
    if "i am want" in t:
        errors.append("❌ 'I am want' → 'I want'")
    return errors

def check_translate(user_txt, variants):
    user_txt = user_txt.lower().strip()
    user_txt = re.sub(r'[^\w\s]', '', user_txt)
    for v in variants:
        v_clean = re.sub(r'[^\w\s]', '', v.lower())
        if user_txt == v_clean or user_txt in v_clean or v_clean in user_txt:
            return True
    return False

user_state = {}

@dp.message(Command("start"))
async def start_cmd(msg):
    uid = msg.from_user.id
    t = random.choice(topics)
    user_state[uid] = {"mode": "normal", "topic": t, "count": 1}
    await msg.answer(
        f"🤖 *English Bot*\n\n*Вопрос 1:*\n{t['q']}\n\n_(перевод: {t['ru']})_",
        parse_mode="Markdown",
        reply_markup=main_keyboard
    )

@dp.message(Command("profile"))
async def profile_cmd(msg):
    uid = msg.from_user.id
    profiles, profile = get_profile(uid)
    xp = profile["xp"]
    lvl, lvl_name = get_level(xp)
    correct = profile["correct"]
    wrong = profile["wrong"]
    total = correct + wrong
    accuracy = int(correct/total*100) if total > 0 else 0
    next_xp = 0
    for l in LEVELS:
        if l["xp"] > xp:
            next_xp = l["xp"]
            break
    if next_xp == 0:
        next_xp = xp
    await msg.answer(
        f"👤 *ПРОФИЛЬ*\n\n🏆 {lvl_name} (ур. {lvl})\n⭐ Опыт: {xp} / {next_xp}\n✅ Правильно: {correct}\n❌ Неправильно: {wrong}\n🎯 Точность: {accuracy}%",
        parse_mode="Markdown"
    )

@dp.message(Command("wordgame"))
async def wordgame_cmd(msg):
    uid = msg.from_user.id
    words = random.sample(all_words, min(10, len(all_words)))
    user_state[uid] = {"mode": "word_game", "words": words, "idx": 0, "score": 0, "dir": random.choice([0,1])}
    w = words[0]
    if user_state[uid]["dir"] == 0:
        await msg.answer(f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇷🇺 {w['ru']} → ?", parse_mode="Markdown")
    else:
        await msg.answer(f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇬🇧 {w['en']} → ?", parse_mode="Markdown")

@dp.message(Command("translategame"))
async def translategame_cmd(msg):
    uid = msg.from_user.id
    sents = random.sample(sentences, min(5, len(sentences)))
    user_state[uid] = {"mode": "translate_game", "sents": sents, "idx": 0, "score": 0}
    s = sents[0]
    await msg.answer(f"📖 *Игра перевод* (+15XP/-5XP)\n\n1/5: 🇬🇧 {s['en']}\n\n✏️ Напиши перевод:", parse_mode="Markdown")

@dp.message(Command("next"))
async def next_cmd(msg):
    uid = msg.from_user.id
    if uid not in user_state:
        await msg.answer("Сначала выбери режим")
        return
    mode = user_state[uid].get("mode")
    user_state[uid]["count"] = user_state[uid].get("count", 0) + 1
    count = user_state[uid]["count"]
    if mode == "normal":
        t = random.choice(topics)
        user_state[uid]["topic"] = t
        await msg.answer(f"*Вопрос {count}:*\n{t['q']}\n\n_(перевод: {t['ru']})_", parse_mode="Markdown")
    elif mode == "easy":
        q = random.choice(easy_q)
        user_state[uid]["current_q"] = q
        await msg.answer(f"🔰 *Вопрос {count}:*\n{q['q']}\n\n_(перевод: {q['ru']})_", parse_mode="Markdown")
    elif mode == "hard":
        q = random.choice(hard_q)
        user_state[uid]["current_q"] = q
        await msg.answer(f"🔥 *Вопрос {count}:*\n{q['q']}\n\n_(перевод: {q['ru']})_", parse_mode="Markdown")

@dp.message(Command("materials"))
async def materials_cmd(msg):
    await msg.answer(
        "📚 *СПРАВОЧНИК*\n\n*Команды:*\n/start - запуск\n/profile - статистика\n/normal - обычные\n/easy - простые\n/hard - сложные\n/test - тест слов\n/wordgame - игра слов\n/translategame - игра перевод\n/next - след. вопрос\n/materials - справочник\n/help - помощь",
        parse_mode="Markdown"
    )

@dp.message(Command("help"))
async def help_cmd(msg):
    await msg.answer("📖 *ПОМОЩЬ*\n\nПросто отвечай на вопросы. Игры дают опыт (XP).\nКоманды: /materials", parse_mode="Markdown")

# КНОПКИ
@dp.message(lambda msg: msg.text == "🇬🇧 Обычный")
async def normal_btn(msg):
    uid = msg.from_user.id
    t = random.choice(topics)
    user_state[uid] = {"mode": "normal", "topic": t, "count": 1}
    await msg.answer(f"*Вопрос:*\n{t['q']}\n\n_(перевод: {t['ru']})_", parse_mode="Markdown")

@dp.message(lambda msg: msg.text == "🎮 Игра слов")
async def wordgame_btn(msg):
    await wordgame_cmd(msg)

@dp.message(lambda msg: msg.text == "📖 Игра перевод")
async def translategame_btn(msg):
    await translategame_cmd(msg)

@dp.message(lambda msg: msg.text == "📝 Тест слов")
async def test_btn(msg):
    await test_cmd(msg)

@dp.message(lambda msg: msg.text == "👤 Профиль")
async def profile_btn(msg):
    await profile_cmd(msg)

@dp.message(lambda msg: msg.text == "🔄 Следующий")
async def next_btn(msg):
    await next_cmd(msg)

@dp.message(lambda msg: msg.text == "📚 Справочник")
async def materials_btn(msg):
    await materials_cmd(msg)

@dp.message(lambda msg: msg.text == "ℹ️ Инфо")
async def info_btn(msg):
    uid = msg.from_user.id
    profiles, profile = get_profile(uid)
    xp = profile["xp"]
    lvl, lvl_name = get_level(xp)
    correct = profile["correct"]
    wrong = profile["wrong"]
    total = correct + wrong
    accuracy = int(correct/total*100) if total > 0 else 0
    next_xp = 0
    for l in LEVELS:
        if l["xp"] > xp:
            next_xp = l["xp"]
            break
    if next_xp == 0:
        next_xp = xp
    levels_text = ""
    for l in LEVELS:
        if xp >= l["xp"]:
            levels_text += f"✅ {l['name']} (ур.{l['level']}) - {l['xp']} XP\n"
        else:
            levels_text += f"⬜ {l['name']} (ур.{l['level']}) - {l['xp']} XP\n"
    await msg.answer(
        f"📋 *ИНФОРМАЦИЯ О БОТЕ*\n\n"
        f"*КОМАНДЫ:*\n/start, /profile, /normal, /easy, /hard, /test, /wordgame, /translategame, /next, /materials, /help\n\n"
        f"*ТВОЙ ПРОГРЕСС:*\n🏆 {lvl_name} (ур. {lvl})\n⭐ Опыт: {xp} / {next_xp}\n✅ Правильно: {correct}\n❌ Неправильно: {wrong}\n🎯 Точность: {accuracy}%\n\n"
        f"*УРОВНИ:*\n{levels_text}\n"
        f"*ЗА ЧТО XP:*\n🎮 Игра слов: +10/-5\n📖 Игра перевод: +15/-5",
        parse_mode="Markdown"
    )

@dp.message(Command("test"))
async def test_cmd(msg):
    uid = msg.from_user.id
    words = random.sample(all_words, min(10, len(all_words)))
    user_state[uid] = {"mode": "test", "words": words, "idx": 0, "score": 0, "dir": random.choice([0,1])}
    w = words[0]
    if user_state[uid]["dir"] == 0:
        await msg.answer(f"📝 *Тест слов*\n\n🇷🇺 {w['ru']} → ?", parse_mode="Markdown")
    else:
        await msg.answer(f"📝 *Тест слов*\n\n🇬🇧 {w['en']} → ?", parse_mode="Markdown")

@dp.message(Command("normal"))
async def normal_cmd(msg):
    uid = msg.from_user.id
    t = random.choice(topics)
    user_state[uid] = {"mode": "normal", "topic": t, "count": 1}
    await msg.answer(f"*Вопрос:*\n{t['q']}\n\n_(перевод: {t['ru']})_", parse_mode="Markdown")

@dp.message(Command("easy"))
async def easy_cmd(msg):
    uid = msg.from_user.id
    q = random.choice(easy_q)
    user_state[uid] = {"mode": "easy", "current_q": q, "count": 1}
    await msg.answer(f"🔰 *Простые вопросы*\n\n{q['q']}\n\n_(перевод: {q['ru']})_", parse_mode="Markdown")

@dp.message(Command("hard"))
async def hard_cmd(msg):
    uid = msg.from_user.id
    q = random.choice(hard_q)
    user_state[uid] = {"mode": "hard", "current_q": q, "count": 1}
    await msg.answer(f"🔥 *Сложные вопросы*\n\n{q['q']}\n\n_(перевод: {q['ru']})_", parse_mode="Markdown")

@dp.message()
async def handle_msg(m):
    uid = m.from_user.id
    answer = m.text.strip()
    if uid not in user_state:
        await m.answer("Нажми /start или выбери режим кнопкой")
        return
    mode = user_state[uid].get("mode")
    
    if mode == "word_game":
        data = user_state[uid]
        idx = data["idx"]
        words = data["words"]
        if idx >= len(words):
            xp_gain = data["score"] * 10
            update_xp(uid, xp_gain)
            await m.answer(f"🎉 Игра окончена! Очки: {data['score']}/10\n+{xp_gain} XP!")
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
            await m.answer(f"✅ +10 XP! ({data['score']}/10)")
        else:
            update_xp(uid, -5)
            if data["dir"] == 0:
                await m.answer(f"❌ -5 XP! {w['ru']} → {w['en']}")
            else:
                await m.answer(f"❌ -5 XP! {w['en']} → {w['ru']}")
        data["idx"] += 1
        if data["idx"] < len(words):
            nw = words[data["idx"]]
            num = data["idx"] + 1
            if data["dir"] == 0:
                await m.answer(f"Слово {num}/10: 🇷🇺 {nw['ru']} → ?")
            else:
                await m.answer(f"Слово {num}/10: 🇬🇧 {nw['en']} → ?")
        else:
            xp_gain = data["score"] * 10
            update_xp(uid, xp_gain)
            await m.answer(f"🎉 Игра окончена! {data['score']}/10\n+{xp_gain} XP!")
            del user_state[uid]
        return
    
    if mode == "translate_game":
        data = user_state[uid]
        idx = data["idx"]
        sents = data["sents"]
        if idx >= len(sents):
            xp_gain = data["score"] * 15
            update_xp(uid, xp_gain)
            await m.answer(f"🎉 Игра окончена! Очки: {data['score']}/5\n+{xp_gain} XP!")
            del user_state[uid]
            return
        s = sents[idx]
        if check_translate(answer, s["ru"]):
            data["score"] += 1
            update_xp(uid, 15)
            await m.answer(f"✅ +15 XP! ({data['score']}/5)")
        else:
            update_xp(uid, -5)
            await m.answer(f"❌ -5 XP! Правильно: {s['ru'][0]}")
        data["idx"] += 1
        if data["idx"] < len(sents):
            ns = sents[data["idx"]]
            num = data["idx"] + 1
            await m.answer(f"Предложение {num}/5: 🇬🇧 {ns['en']}\n\n✏️ Перевод:")
        else:
            xp_gain = data["score"] * 15
            update_xp(uid, xp_gain)
            await m.answer(f"🎉 Игра окончена! {data['score']}/5\n+{xp_gain} XP!")
            del user_state[uid]
        return
    
    if mode == "test":
        data = user_state[uid]
        idx = data["idx"]
        words = data["words"]
        if idx >= len(words):
            await m.answer(f"📝 Тест окончен! Результат: {data['score']}/{len(words)}")
            del user_state[uid]
            return
        w = words[idx]
        if data["dir"] == 0:
            correct = answer.lower().strip() == w["en"].lower()
        else:
            correct = answer.lower().strip() == w["ru"].lower()
        if correct:
            data["score"] += 1
            await m.answer("✅ Правильно!")
        else:
            if data["dir"] == 0:
                await m.answer(f"❌ {w['ru']} → {w['en']}")
            else:
                await m.answer(f"❌ {w['en']} → {w['ru']}")
        data["idx"] += 1
        if data["idx"] < len(words):
            nw = words[data["idx"]]
            num = data["idx"] + 1
            if data["dir"] == 0:
                await m.answer(f"Слово {num}: 🇷🇺 {nw['ru']} → ?")
            else:
                await m.answer(f"Слово {num}: 🇬🇧 {nw['en']} → ?")
        else:
            await m.answer(f"📝 Тест окончен! {data['score']}/{len(words)}")
            del user_state[uid]
        return
    
    if mode == "normal":
        topic = user_state[uid].get("topic")
        if not topic:
            await m.answer("Ошибка, нажми /start")
            return
        keywords = topic.get("kw", [])
        matched = [kw for kw in keywords if kw in answer.lower()]
        is_relevant = len(matched) > 0 or len(answer.split()) >= 4
        errors = check_grammar(answer)
        response = f"📝 *{answer}*\n\n"
        response += "✅ Смысл верен\n" if is_relevant else "⚠️ Не по теме\n"
        if errors:
            response += "\n" + "\n".join(errors)
        else:
            response += "✅ Грамматика верна"
        await m.answer(response, parse_mode="Markdown")
        new_t = random.choice(topics)
        user_state[uid]["topic"] = new_t
        await m.answer(f"🔹 *Следующий вопрос:*\n{new_t['q']}\n\n_(перевод: {new_t['ru']})_", parse_mode="Markdown")

async def main():
    print(f"✅ Бот запущен! {len(all_words)} слов, RPG система активна")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
