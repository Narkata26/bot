from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, ConversationHandler
import qrcode
from io import BytesIO

# 🔐 Bot Token — შეცვალე შენსით
TOKEN = '8010639248:AAE465KndkDhE1jJ2tKUQjMqGShNsY-y09k'

# 💲 პროდუქციის სია დოლარში
PRODUCTS = {
    "1gr OG KUSH HIGH QUALITY (Indoor)": 30.0,
    "0.5gr Blue Dream ": 20.0,
    "1gr Girl Scout Cookies (GSC)": 39.0,
    "2gr AK-47 - Indica ": 60,
    "1gr Pineapple Express": 40,
}

# 🌆 ქალაქები და უბნები
CITIES = {
    "Tbilisi": ["ვაკე", "საბურთალო", "გლდანი"],
    "Batumi": ["ანგისა", "ჩაქვი", "მახინჯაური"],
    "Kutaisi": ["ბაგრატის უბანი", "დავით აღმაშენებლის ქუჩა"],
    "Kobuleti": ["ცენტრი", "პატარა კახეთი"],
    "Poti": ["ძველი პორტი", "ახალი უბანი"],
    "Rustavi": ["მეორე მიკრო", "მეშვიდე მიკრო"],
    "Senaki": ["ცენტრი", "ავანგარდი"],
    "Gori": ["ციხის უბანი", "ჭავჭავაძის ქუჩა"]
}

# Conversation States
CITY, PRODUCT, NEIGHBORHOOD = range(3)

# 🏠 LiteCoin მისამართი
LTC_ADDRESS = "LRyr8QVgrqnLnWBywP3vtSz7EUktjTMWae"  # აქ ჩასვით თქვენი LiteCoin მისამართი

# 🖼️ QR კოდის გენერაცია
def generate_qr(payment_amount):
    # LiteCoin გადახდის ინფორმაცია
    payment_url = f"litecoin:{LTC_ADDRESS}?amount={payment_amount}"
    
    # QR კოდის გენერაცია
    qr = qrcode.make(payment_url)
    bio = BytesIO()
    qr.save(bio, format="PNG")
    bio.seek(0)
    return bio

# ✅ /start — ქალაქის არჩევა
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[city] for city in CITIES]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("გამარჯობა! აირჩიე ქალაქი:", reply_markup=reply_markup)
    return CITY

# ✅ ქალაქის არჩევა — ინახავს და აჩვენებს ყველა პროდუქტს
async def handle_city_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text.strip()
    if city in CITIES:
        context.user_data["city"] = city
        keyboard = [[f"{name} - {price}$"] for name, price in PRODUCTS.items()]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"{city}-ში ხელმისაწვდომია შემდეგი პროდუქტები:", reply_markup=reply_markup)
        return PRODUCT
    else:
        await update.message.reply_text("გთხოვ, აირჩიე ქალაქი სიიდან /start.")
        return CITY

# ✅ პროდუქტის არჩევა — უბნების ჩვენება
async def handle_product_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = context.user_data.get("city")
    if not city:
        await update.message.reply_text("გთხოვ, ჯერ აირჩიე ქალაქი /start-ით.")
        return CITY

    text = update.message.text.strip()
    product_name = text.split(" -")[0]

    if product_name in PRODUCTS:
        context.user_data["product"] = product_name
        neighborhoods = CITIES[city]
        keyboard = [[n] for n in neighborhoods]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(f"აირჩიე უბანი {product_name}-ის მისაღებად {city}-ში:", reply_markup=reply_markup)
        return NEIGHBORHOOD
    else:
        await update.message.reply_text("პროდუქტი არ მოიძებნა. სცადე ხელახლა.")
        return PRODUCT

# ✅ უბნის არჩევის შემდეგ — გადახდა
async def handle_neighborhood_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = context.user_data.get("city")
    product = context.user_data.get("product")
    neighborhood = update.message.text.strip()

    if city and product and neighborhood in CITIES[city]:
        # ხელმისაწვდომია გადახდის პროცესი
        product_price_usd = PRODUCTS[product]
        product_price_ltc = product_price_usd * 0.011662487608606916   # 30$ = 0.33195749 LTC

        # QR კოდის გენერირება
        qr_image = generate_qr(product_price_ltc)

        # გადახდის პროცედურის დაწყება
        await update.message.reply_text(
    f"✅ შენ აირჩიე: {product}\n"
    f"📍 ქალაქი: {city}\n"
    f"🏘️ უბანი: {neighborhood}\n"
    f"🛒 პროდუქტი გამოგზავნილია!\n"
    f"💲 ფასია: {product_price_usd}$\n"
    f"🛒 გადახდის ოდენობა: {product_price_ltc:.8f} LTC\n"
    f"🔗 LiteCoin მისამართი: {LTC_ADDRESS}\n"
    f"🛍️ გადახდის შემდეგ დააჭირეთ ღილაკს (გადახდა) რომ დაგენერირდეს ადრესი!",
    reply_markup=ReplyKeyboardMarkup([['გადახდა']], resize_keyboard=True)
)
        await update.message.reply_photo(photo=qr_image)
        return ConversationHandler.END
    else:
        await update.message.reply_text("გთხოვ, აირჩიე უბანი ჩამონათვალიდან.")
        return NEIGHBORHOOD

# ✅ აბლოკება როდესაც საუბარი დასრულდება
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("საუბარი გაუქმდა.")
    return ConversationHandler.END

# ▶️ აპლიკაციის გაშვება
app = ApplicationBuilder().token(TOKEN).build()

# ConversationHandler to manage the flow
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city_choice)],
        PRODUCT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_product_choice)],
        NEIGHBORHOOD: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_neighborhood_choice)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

# 🔗 ჰენდლერები
app.add_handler(conv_handler)

# 🚀 გაშვება
app.run_polling()
