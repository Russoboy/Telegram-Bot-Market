import telebot
import sqlite3

# Replace with your Telegram bot token
BOT_TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # Replace with your Telegram user ID

bot = telebot.TeleBot(BOT_TOKEN)

# Database setup
conn = sqlite3.connect("store.db", check_same_thread=False)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    price INTEGER,
    link TEXT
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    product_name TEXT,
    status TEXT
)
''')
conn.commit()

# Command: /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, "👋 Welcome to MOD & Games Store!\nUse /shop to view available products.")

# Command: /shop
@bot.message_handler(commands=['shop'])
def show_products(message):
    cursor.execute("SELECT name, price FROM products")
    products = cursor.fetchall()

    if not products:
        bot.send_message(message.chat.id, "😢 No products available at the moment.")
        return

    response = "🛒 Available Products:\n\n"
    for name, price in products:
        response += f"🎮 {name} - ${price}\n"
    response += "\nReply with the product name to order."
    bot.send_message(message.chat.id, response)

# Handle product selection
@bot.message_handler(func=lambda message: True)
def process_order(message):
    cursor.execute("SELECT * FROM products WHERE name = ?", (message.text,))
    product = cursor.fetchone()

    if product:
        cursor.execute("INSERT INTO orders (user_id, product_name, status) VALUES (?, ?, ?)", 
                       (message.chat.id, message.text, "Pending"))
        conn.commit()
        bot.send_message(
            message.chat.id,
            f"✅ {message.text} costs ${product[2]}\n"
            "💰 Send payment and reply with 'PAID' to confirm your order."
        )
    elif message.text.lower() == "paid":
        confirm_payment(message)
    else:
        bot.send_message(message.chat.id, "❌ Invalid selection. Use /shop to see available products.")

# Confirm payment
def confirm_payment(message):
    cursor.execute("SELECT * FROM orders WHERE user_id = ? AND status = ?", (message.chat.id, "Pending"))
    order = cursor.fetchone()

    if order:
        cursor.execute("UPDATE orders SET status = 'Paid' WHERE id = ?", (order[0],))
        conn.commit()
        
        cursor.execute("SELECT link FROM products WHERE name = ?", (order[2],))
        product_link = cursor.fetchone()

        bot.send_message(message.chat.id, f"💾 Payment confirmed! Here is your download link: {product_link[0]}")
    else:
        bot.send_message(message.chat.id, "❌ No pending payments found.")

# Admin Command: Add Product
@bot.message_handler(commands=['add'])
def add_product(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this command.")
        return

    msg = bot.send_message(message.chat.id, "Enter product details (Name, Price, Download Link) separated by commas:")
    bot.register_next_step_handler(msg, save_product)

def save_product(message):
    try:
        name, price, link = message.text.split(",")
        cursor.execute("INSERT INTO products (name, price, link) VALUES (?, ?, ?)", (name.strip(), int(price.strip()), link.strip()))
        conn.commit()
        bot.send_message(message.chat.id, "✅ Product added successfully!")
    except:
        bot.send_message(message.chat.id, "❌ Invalid format. Use: Name, Price, Link")

# Admin Command: Remove Product
@bot.message_handler(commands=['remove'])
def remove_product(message):
    if message.chat.id != ADMIN_ID:
        bot.send_message(message.chat.id, "🚫 You are not authorized to use this command.")
        return

    msg = bot.send_message(message.chat.id, "Enter the name of the product to remove:")
    bot.register_next_step_handler(msg, delete_product)

def delete_product(message):
    cursor.execute("DELETE FROM products WHERE name = ?", (message.text,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Product removed successfully!")

# Run the bot
bot.polling()
