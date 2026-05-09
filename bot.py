import os
import json
import random
import time
import re
import urllib.request

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    print("❌ Ошибка: BOT_TOKEN не задан!")
    exit(1)

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"
LAST_UPDATE_ID = 0

# ==================== ЗАГРУЗКА СЛОВ ====================
def load_words():
    words = []
    try:
        with open("words.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and "," in line:
                    parts = line.split(",")
                    words.append({"ru": parts[0].strip(), "en": parts[1].strip()})
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
    profiles = {}
    if os.path.exists(PROFILES_FILE):
        try:
            with open(PROFILES_FILE, "r") as f:
                profiles = json.load(f)
        except:
            profiles = {}
    uid = str(user_id)
    if uid not in profiles:
        profiles[uid] = {"xp": 0, "correct": 0, "wrong": 0}
    return profiles, profiles[uid]

def save_profile(profiles):
    try:
        with open(PROFILES_FILE, "w") as f:
            json.dump(profiles, f, indent=2)
    except:
        pass

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
    {"q": "What did you eat for breakfast today?", "kw": ["eat","ate","breakfast","food","rice","bread","egg","milk"], "ru": "Что ты ел на завтрак?"},
    {"q": "What is your favorite food? Why?", "kw": ["favorite","food","like","love","pizza","pasta","chocolate"], "ru": "Твоя любимая еда?"},
    {"q": "What is your hobby? Why do you like it?", "kw": ["hobby","like","love","play","read","draw","sing"], "ru": "Твоё хобби?"},
    {"q": "Where would you like to travel? Why?", "kw": ["travel","go","visit","country","beach","mountain"], "ru": "Куда хочешь поехать?"},
    {"q": "Describe your best friend.", "kw": ["friend","best","kind","funny","smart","loyal"], "ru": "Опиши лучшего друга."},
    {"q": "How many people are in your family?", "kw": ["family","people","mother","father","sister","brother"], "ru": "Сколько человек в семье?"},
    {"q": "What do you want to be in the future?", "kw": ["future","want","be","doctor","teacher","engineer"], "ru": "Кем хочешь стать?"},
    {"q": "Do you play any sports? What?", "kw": ["sport","play","football","soccer","basketball","tennis"], "ru": "Твой любимый спорт?"},
    {"q": "What kind of movies do you like?", "kw": ["movie","film","like","comedy","action","drama"], "ru": "Любимые фильмы?"},
    {"q": "What is your favorite animal? Why?", "kw": ["animal","favorite","dog","cat","lion","tiger"], "ru": "Любимое животное?"},
    {"q": "Do you like listening to music? What genre?", "kw": ["music","listen","like","song","pop","rock","rap"], "ru": "Любимая музыка?"},
    {"q": "What is your favorite season? Why?", "kw": ["season","summer","winter","spring","autumn","sun","snow"], "ru": "Любимое время года?"},
    {"q": "Do you like reading books? What kind?", "kw": ["read","reading","book","novel","story","fiction"], "ru": "Любишь читать книги?"},
    {"q": "What do you do in your free time?", "kw": ["free","time","weekend","relax","hobby","walk","sleep"], "ru": "Что делаешь в свободное время?"},
    {"q": "Do you prefer city or countryside? Why?", "kw": ["city","countryside","village","prefer","quiet","noisy"], "ru": "Город или деревня?"},
    {"q": "What is your favorite drink?", "kw": ["drink","favorite","water","juice","coffee","tea","soda"], "ru": "Любимый напиток?"},
    {"q": "Do you like cooking? What can you cook?", "kw": ["cook","cooking","like","make","prepare","kitchen","dish"], "ru": "Любишь готовить?"},
    {"q": "Do you like shopping? Where do you shop?", "kw": ["shop","shopping","like","buy","store","mall","online"], "ru": "Любишь ходить по магазинам?"},
    {"q": "How often do you use the internet?", "kw": ["internet","use","often","every day","online","web"], "ru": "Как часто пользуешься интернетом?"},
    {"q": "What is your favorite weather? Why?", "kw": ["weather","sunny","rainy","cloudy","snowy","warm","cold"], "ru": "Любимая погода?"},
    {"q": "Do you like rain? Why or why not?", "kw": ["rain","rainy","like","dont like","wet","umbrella","cold"], "ru": "Нравится ли тебе дождь?"},
    {"q": "Do you have any pets? Describe them.", "kw": ["pet","animal","dog","cat","bird","fish","hamster"], "ru": "Есть ли у тебя питомцы?"},
    {"q": "Who is your role model? Why?", "kw": ["role","model","hero","admire","respect","mother","father"], "ru": "Кто твой кумир?"},
    {"q": "Do you have many friends? What do you do together?", "kw": ["friend","many","together","hang out","walk","play"], "ru": "Что вы делаете с друзьями?"},
    {"q": "What is your favorite subject at school? Why?", "kw": ["subject","school","like","math","english","history"], "ru": "Любимый предмет в школе?"},
    {"q": "What do you do to improve your English?", "kw": ["english","improve","learn","study","practice","speak"], "ru": "Как учишь английский?"},
    {"q": "How often do you exercise?", "kw": ["exercise","workout","gym","run","swim","walk","often"], "ru": "Как часто занимаешься спортом?"},
    {"q": "What is your favorite holiday? Why?", "kw": ["holiday","favorite","new year","christmas","birthday","celebrate"], "ru": "Любимый праздник?"},
]

easy_q = [
    {"q": "What is your name?", "ru": "Как тебя зовут?"},
    {"q": "How old are you?", "ru": "Сколько тебе лет?"},
    {"q": "Where are you from?", "ru": "Откуда ты?"},
    {"q": "Do you like cats or dogs?", "ru": "Кошки или собаки?"},
    {"q": "What is your favorite color?", "ru": "Твой любимый цвет?"},
    {"q": "Do you like pizza?", "ru": "Любишь пиццу?"},
]

hard_q = [
    {"q": "What would you do if you won a million dollars?", "ru": "Что бы сделал с миллионом долларов?"},
    {"q": "Describe a person who inspires you and why.", "ru": "Опиши человека, который вдохновляет тебя."},
    {"q": "What is the most important lesson life has taught you?", "ru": "Какой самый важный урок преподала тебе жизнь?"},
    {"q": "If you could change one thing about the world, what would it be?", "ru": "Если бы ты мог изменить одну вещь в мире, что бы это было?"},
]

translate_sentences = [
    {"en": "Hello, how are you?", "ru": ["привет как дела", "здравствуй как ты", "привет как ты"]},
    {"en": "I like to read books in the evening.", "ru": ["я люблю читать книги вечером", "мне нравится читать книги по вечерам"]},
    {"en": "What time do you usually wake up?", "ru": ["во сколько ты обычно просыпаешься", "в котором часу ты обычно встаешь"]},
    {"en": "She is my best friend from school.", "ru": ["она моя лучшая подруга со школы", "она моя лучшая подруга из школы"]},
    {"en": "It is very cold outside today.", "ru": ["сегодня на улице очень холодно", "на улице сегодня очень холодно"]},
    {"en": "I want to learn English.", "ru": ["я хочу выучить английский", "хочу учить английский"]},
    {"en": "Can you help me?", "ru": ["ты можешь помочь мне", "можешь помочь мне"]},
    {"en": "I am going to visit my grandmother.", "ru": ["я собираюсь навестить бабушку", "я навещу бабушку"]},
    {"en": "This is the best pizza.", "ru": ["это лучшая пицца", "это самая лучшая пицца"]},
    {"en": "What are you doing?", "ru": ["что ты делаешь", "чем ты занимаешься"]},
]

# ==================== ПРОВЕРКИ ====================
def check_grammar(txt):
    errors = []
    t = txt.lower().strip()
    if len(t) < 2:
        errors.append("❌ Вы ничего не написали.")
        return errors
    if len(t.split()) < 3:
        errors.append("⚠️ Ответ слишком короткий. Напишите 3+ слова.")
    if re.search(r'[а-яё]', t, re.IGNORECASE):
        errors.append("❌ Обнаружены русские буквы. Пишите только на английском!")
    if txt and txt[0].islower():
        errors.append("📌 Начинайте предложение с заглавной буквы.")
    if "i am like" in t:
        errors.append("❌ 'I am like' → 'I like'")
    if "i am want" in t:
        errors.append("❌ 'I am want' → 'I want'")
    if re.search(r"\bwant\s+[a-z]+\b", t) and "want to" not in t:
        errors.append("❌ 'I want go' → 'I want TO go'")
    if re.search(r"i have (\d+) years?", t) and "old" not in t:
        errors.append("❌ 'I have X years' → 'I am X years old'")
    if "i am agree" in t:
        errors.append("❌ 'I am agree' → 'I agree'")
    return errors

def check_translate(user_txt, variants):
    user_txt = user_txt.lower().strip()
    user_txt = re.sub(r'[^\w\s]', '', user_txt)
    for v in variants:
        v_clean = v.lower().strip()
        v_clean = re.sub(r'[^\w\s]', '', v_clean)
        if user_txt == v_clean or user_txt in v_clean or v_clean in user_txt:
            return True
    return False

def check_meaning(answer, keywords):
    answer_lower = answer.lower()
    matched = [kw for kw in keywords if re.search(rf'\b{re.escape(kw)}\b', answer_lower)]
    score = len(matched)
    word_count = len(answer.split())
    if word_count >= 5 and score >= 2:
        return True, matched
    if score >= 1:
        return True, matched
    return False, matched

user_state = {}

def send_message(chat_id, text, reply_markup=None):
    data = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        data["reply_markup"] = json.dumps(reply_markup)
    try:
        req = urllib.request.Request(f"{API_URL}/sendMessage", data=json.dumps(data).encode(), headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=30)
    except Exception as e:
        print(f"Ошибка отправки: {e}")

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "🇬🇧 Обычный"}, {"text": "🔰 Простой"}],
            [{"text": "🔥 Сложный"}, {"text": "🎮 Игра слов"}],
            [{"text": "📖 Игра перевод"}, {"text": "📝 Тест слов"}],
            [{"text": "👤 Профиль"}, {"text": "📚 Справочник"}],
            [{"text": "🔄 Следующий"}, {"text": "ℹ️ Инфо"}]
        ],
        "resize_keyboard": True
    }

# ==================== ОБРАБОТКА (С ИСПРАВЛЕНИЕМ ДВОЙНЫХ СООБЩЕНИЙ) ====================
def process_message(chat_id, user_id, text):
    try:
        # Проверяем, что это не ответ на игру или тест
        is_in_game = False
        if user_id in user_state:
            mode = user_state[user_id].get("mode")
            if mode in ["word_game", "translate_game", "test"]:
                is_in_game = True
        
        # Обработка команд через /
        if text == "/start":
            user_state[user_id] = {"mode": "normal", "question_count": 1}
            t = random.choice(topics)
            user_state[user_id]["current_topic"] = t
            send_message(chat_id,
                f"🤖 *English Bot*\n\n"
                f"Выбери режим кнопками:\n\n"
                f"*Вопрос 1:*\n{t['q']}\n\n_(перевод: {t['ru']})_",
                reply_markup=get_main_keyboard())
            return
        
        if text == "/profile":
            profiles, profile = get_profile(user_id)
            xp = profile["xp"]
            lvl, lvl_name = get_level(xp)
            correct = profile["correct"]
            wrong = profile["wrong"]
            total = correct + wrong
            accuracy = int(correct/total*100) if total > 0 else 0
            send_message(chat_id,
                f"👤 *ПРОФИЛЬ*\n\n"
                f"🏆 {lvl_name} (ур. {lvl})\n"
                f"⭐ Опыт: {xp}\n"
                f"✅ Правильно: {correct}\n"
                f"❌ Неправильно: {wrong}\n"
                f"🎯 Точность: {accuracy}%")
            return
        
        # Кнопки (только если не в игре)
        if not is_in_game:
            if text == "🇬🇧 Обычный":
                user_state[user_id] = {"mode": "normal", "question_count": 1}
                t = random.choice(topics)
                user_state[user_id]["current_topic"] = t
                send_message(chat_id, f"*Вопрос 1:*\n{t['q']}\n\n_(перевод: {t['ru']})_")
                return
            
            if text == "🔰 Простой":
                user_state[user_id] = {"mode": "easy", "question_count": 1}
                q = random.choice(easy_q)
                user_state[user_id]["current_question"] = q
                send_message(chat_id, f"🔰 *Простой режим*\n\n{q['q']}\n\n_(перевод: {q['ru']})_")
                return
            
            if text == "🔥 Сложный":
                user_state[user_id] = {"mode": "hard", "question_count": 1}
                q = random.choice(hard_q)
                user_state[user_id]["current_question"] = q
                send_message(chat_id, f"🔥 *Сложный режим*\n\n{q['q']}\n\n_(перевод: {q['ru']})_")
                return
            
            if text == "🎮 Игра слов":
                words = random.sample(all_words, min(10, len(all_words)))
                user_state[user_id] = {"mode": "word_game", "words": words, "idx": 0, "score": 0, "dir": random.choice([0,1])}
                w = words[0]
                if user_state[user_id]["dir"] == 0:
                    send_message(chat_id, f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇷🇺 {w['ru']} → ?")
                else:
                    send_message(chat_id, f"🎮 *Игра слов* (+10XP/-5XP)\n\n1/10: 🇬🇧 {w['en']} → ?")
                return
            
            if text == "📖 Игра перевод":
                sents = random.sample(translate_sentences, min(5, len(translate_sentences)))
                user_state[user_id] = {"mode": "translate_game", "sents": sents, "idx": 0, "score": 0}
                s = sents[0]
                send_message(chat_id, f"📖 *Игра перевод* (+15XP/-5XP)\n\n1/5: 🇬🇧 {s['en']}\n\n✏️ Напиши перевод:")
                return
            
            if text == "📝 Тест слов":
                words = random.sample(all_words, min(10, len(all_words)))
                user_state[user_id] = {"mode": "test", "words": words, "idx": 0, "score": 0, "dir": random.choice([0,1])}
                w = words[0]
                if user_state[user_id]["dir"] == 0:
                    send_message(chat_id, f"📝 *Тест слов*\n\n1/10: 🇷🇺 {w['ru']} → ?")
                else:
                    send_message(chat_id, f"📝 *Тест слов*\n\n1/10: 🇬🇧 {w['en']} → ?")
                return
            
            if text == "👤 Профиль":
                profiles, profile = get_profile(user_id)
                xp = profile["xp"]
                lvl, lvl_name = get_level(xp)
                correct = profile["correct"]
                wrong = profile["wrong"]
                total = correct + wrong
                accuracy = int(correct/total*100) if total > 0 else 0
                send_message(chat_id, f"👤 *ПРОФИЛЬ*\n\n🏆 {lvl_name} (ур. {lvl})\n⭐ Опыт: {xp}\n✅ Правильно: {correct}\n❌ Неправильно: {wrong}\n🎯 Точность: {accuracy}%")
                return
            
            if text == "📚 Справочник":
                send_message(chat_id,
                    "📚 *СПРАВОЧНИК*\n\n"
                    "*Режимы:*\n"
                    "🇬🇧 Обычный - 50+ тем\n"
                    "🔰 Простой - лёгкие вопросы\n"
                    "🔥 Сложный - глубокие вопросы\n"
                    "🎮 Игра слов - перевод слов (+10XP/-5XP)\n"
                    "📖 Игра перевод - перевод предложений (+15XP/-5XP)\n"
                    "📝 Тест слов - быстрый тест\n\n"
                    "*Команды:* /start, /profile")
                return
            
            if text == "🔄 Следующий":
                if user_id not in user_state:
                    send_message(chat_id, "Сначала выбери режим кнопкой")
                    return
                mode = user_state[user_id].get("mode")
                if mode not in ["normal", "easy", "hard"]:
                    send_message(chat_id, "Сначала выбери режим: Обычный, Простой или Сложный")
                    return
                if "question_count" not in user_state[user_id]:
                    user_state[user_id]["question_count"] = 1
                user_state[user_id]["question_count"] += 1
                count = user_state[user_id]["question_count"]
                if mode == "normal":
                    t = random.choice(topics)
                    user_state[user_id]["current_topic"] = t
                    send_message(chat_id, f"*Вопрос {count}:*\n{t['q']}\n\n_(перевод: {t['ru']})_")
                elif mode == "easy":
                    q = random.choice(easy_q)
                    user_state[user_id]["current_question"] = q
                    send_message(chat_id, f"🔰 *Вопрос {count}:*\n{q['q']}\n\n_(перевод: {q['ru']})_")
                elif mode == "hard":
                    q = random.choice(hard_q)
                    user_state[user_id]["current_question"] = q
                    send_message(chat_id, f"🔥 *Вопрос {count}:*\n{q['q']}\n\n_(перевод: {q['ru']})_")
                return
            
            if text == "ℹ️ Инфо":
                levels_text = "\n".join([f"{l['level']}. {l['name']} - {l['xp']} XP" for l in LEVELS])
                profiles, profile = get_profile(user_id)
                xp = profile["xp"]
                lvl, lvl_name = get_level(xp)
                send_message(chat_id,
                    f"📋 *ИНФОРМАЦИЯ*\n\n"
                    f"*Твой уровень:* {lvl_name} (ур. {lvl})\n"
                    f"*Твой опыт:* {xp} XP\n\n"
                    f"*Все уровни:*\n{levels_text}\n\n"
                    f"*За что XP:*\n🎮 Игра слов: +10/-5\n📖 Игра перевод: +15/-5\n\n"
                    f"*Команды:* /start, /profile")
                return
        
        # Обработка ответов в играх
        if user_id in user_state:
            mode = user_state[user_id].get("mode")
            
            # ИГРА СЛОВ
            if mode == "word_game":
                data = user_state[user_id]
                idx = data["idx"]
                words = data["words"]
                if idx >= len(words):
                    xp_gain = data["score"] * 10
                    update_xp(user_id, xp_gain)
                    send_message(chat_id, f"🎉 Игра окончена! Очки: {data['score']}/{len(words)}\n+{xp_gain} XP!", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                    return
                w = words[idx]
                if data["dir"] == 0:
                    correct = text.lower().strip() == w["en"].lower()
                else:
                    correct = text.lower().strip() == w["ru"].lower()
                if correct:
                    data["score"] += 1
                    update_xp(user_id, 10)
                    send_message(chat_id, f"✅ +10 XP! ({data['score']}/{len(words)})")
                else:
                    update_xp(user_id, -5)
                    if data["dir"] == 0:
                        send_message(chat_id, f"❌ -5 XP! {w['ru']} → {w['en']}")
                    else:
                        send_message(chat_id, f"❌ -5 XP! {w['en']} → {w['ru']}")
                data["idx"] += 1
                if data["idx"] < len(words):
                    nw = words[data["idx"]]
                    num = data["idx"] + 1
                    if data["dir"] == 0:
                        send_message(chat_id, f"Слово {num}/{len(words)}: 🇷🇺 {nw['ru']} → ?")
                    else:
                        send_message(chat_id, f"Слово {num}/{len(words)}: 🇬🇧 {nw['en']} → ?")
                else:
                    xp_gain = data["score"] * 10
                    update_xp(user_id, xp_gain)
                    send_message(chat_id, f"🎉 Игра окончена! {data['score']}/{len(words)}\n+{xp_gain} XP!", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                return
            
            # ИГРА ПЕРЕВОД
            if mode == "translate_game":
                data = user_state[user_id]
                idx = data["idx"]
                sents = data["sents"]
                if idx >= len(sents):
                    xp_gain = data["score"] * 15
                    update_xp(user_id, xp_gain)
                    send_message(chat_id, f"🎉 Игра окончена! Очки: {data['score']}/{len(sents)}\n+{xp_gain} XP!", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                    return
                s = sents[idx]
                if check_translate(text, s["ru"]):
                    data["score"] += 1
                    update_xp(user_id, 15)
                    send_message(chat_id, f"✅ +15 XP! ({data['score']}/{len(sents)})")
                else:
                    update_xp(user_id, -5)
                    send_message(chat_id, f"❌ -5 XP! Правильно: {s['ru'][0]}")
                data["idx"] += 1
                if data["idx"] < len(sents):
                    ns = sents[data["idx"]]
                    num = data["idx"] + 1
                    send_message(chat_id, f"Предложение {num}/{len(sents)}: 🇬🇧 {ns['en']}\n\n✏️ Напиши перевод:")
                else:
                    xp_gain = data["score"] * 15
                    update_xp(user_id, xp_gain)
                    send_message(chat_id, f"🎉 Игра окончена! {data['score']}/{len(sents)}\n+{xp_gain} XP!", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                return
            
            # ТЕСТ СЛОВ
            if mode == "test":
                data = user_state[user_id]
                idx = data["idx"]
                words = data["words"]
                if idx >= len(words):
                    send_message(chat_id, f"📝 Тест окончен! Результат: {data['score']}/{len(words)}", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                    return
                w = words[idx]
                if data["dir"] == 0:
                    correct = text.lower().strip() == w["en"].lower()
                else:
                    correct = text.lower().strip() == w["ru"].lower()
                if correct:
                    data["score"] += 1
                    send_message(chat_id, f"✅ Правильно! ({data['score']}/{len(words)})")
                else:
                    if data["dir"] == 0:
                        send_message(chat_id, f"❌ Неправильно! {w['ru']} → {w['en']}")
                    else:
                        send_message(chat_id, f"❌ Неправильно! {w['en']} → {w['ru']}")
                data["idx"] += 1
                if data["idx"] < len(words):
                    nw = words[data["idx"]]
                    num = data["idx"] + 1
                    if data["dir"] == 0:
                        send_message(chat_id, f"Слово {num}/{len(words)}: 🇷🇺 {nw['ru']} → ?")
                    else:
                        send_message(chat_id, f"Слово {num}/{len(words)}: 🇬🇧 {nw['en']} → ?")
                else:
                    send_message(chat_id, f"📝 Тест окончен! Результат: {data['score']}/{len(words)}", reply_markup=get_main_keyboard())
                    del user_state[user_id]
                return
            
            # ОБЫЧНЫЙ РЕЖИМ
            if mode == "normal" and not is_in_game:
                topic = user_state[user_id].get("current_topic")
                if topic:
                    keywords = topic.get("kw", [])
                    is_relevant, matched = check_meaning(text, keywords)
                    grammar_errors = check_grammar(text)
                    response = f"📝 *{text}*\n\n"
                    if is_relevant:
                        response += "✅ *Смысл верный!*\n"
                    else:
                        response += "⚠️ *Ответ не по теме*\n"
                    if grammar_errors:
                        response += "\n⚠️ *Грамматика:*\n" + "\n".join(grammar_errors)
                    else:
                        if len(text.split()) >= 3:
                            response += "✅ *Грамматика правильная!*"
                    send_message(chat_id, response)
                    new_t = random.choice(topics)
                    user_state[user_id]["current_topic"] = new_t
                    user_state[user_id]["question_count"] = user_state[user_id].get("question_count", 0) + 1
                    send_message(chat_id, f"🔹 *Следующий вопрос ({user_state[user_id]['question_count']}):*\n{new_t['q']}\n\n_(перевод: {new_t['ru']})_")
                return
            
            # ПРОСТОЙ РЕЖИМ
            if mode == "easy" and not is_in_game:
                grammar_errors = check_grammar(text)
                if grammar_errors:
                    send_message(chat_id, "\n".join(grammar_errors))
                else:
                    send_message(chat_id, "✅ *Отлично!*")
                new_q = random.choice(easy_q)
                user_state[user_id]["current_question"] = new_q
                user_state[user_id]["question_count"] = user_state[user_id].get("question_count", 0) + 1
                send_message(chat_id, f"🔰 *Вопрос {user_state[user_id]['question_count']}:*\n{new_q['q']}\n\n_(перевод: {new_q['ru']})_")
                return
            
            # СЛОЖНЫЙ РЕЖИМ
            if mode == "hard" and not is_in_game:
                grammar_errors = check_grammar(text)
                response = f"📝 *{text}*\n\n"
                if len(text.split()) < 8:
                    response += "⚠️ *Короткий ответ (нужно 8+ слов)*\n"
                if grammar_errors:
                    response += "\n⚠️ *Грамматика:*\n" + "\n".join(grammar_errors)
                else:
                    if len(text.split()) >= 8:
                        response += "✅ *Отличный развёрнутый ответ!*"
                send_message(chat_id, response)
                new_q = random.choice(hard_q)
                user_state[user_id]["current_question"] = new_q
                user_state[user_id]["question_count"] = user_state[user_id].get("question_count", 0) + 1
                send_message(chat_id, f"🔥 *Вопрос {user_state[user_id]['question_count']}:*\n{new_q['q']}\n\n_(перевод: {new_q['ru']})_")
                return
        
        # Если ничего не подошло
        if not is_in_game and user_id not in user_state:
            send_message(chat_id, "Нажми /start или выбери режим кнопкой", reply_markup=get_main_keyboard())
    
    except Exception as e:
        print(f"Ошибка: {e}")
        send_message(chat_id, "❌ Ошибка. Попробуй /start")

# ==================== ПОЛЛИНГ ====================
def get_updates(offset=None):
    url = f"{API_URL}/getUpdates?timeout=30"
    if offset:
        url += f"&offset={offset}"
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=35) as response:
            return json.loads(response.read())
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

def main():
    global LAST_UPDATE_ID
    print("=" * 40)
    print("🤖 ENGLISH BOT ЗАПУЩЕН")
    print(f"✅ Слов: {len(all_words)}")
    print(f"✅ Тем: {len(topics)}")
    print("=" * 40)
    
    while True:
        try:
            updates = get_updates(LAST_UPDATE_ID + 1 if LAST_UPDATE_ID else None)
            if updates and updates.get("ok"):
                for update in updates.get("result", []):
                    LAST_UPDATE_ID = update.get("update_id")
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]
                        text = msg.get("text", "")
                        process_message(chat_id, user_id, text)
            time.sleep(1)
        except Exception as e:
            print(f"Ошибка: {e}")
            time.sleep(5)

if __name__ == "__main__":
    main()
