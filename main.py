from remotekakao.bot import Bot

bot = Bot(prefix="!")


@bot.route(cmd="ping", room=["test room"])
def ping(room, msg, sender, is_group_chat, *args):
    return "pong"


@bot.route(cmd="echo", prefix='@', room=["test room"])
def echo(room, msg, sender, is_group_chat, *args):
    return msg


@bot.on_msg()
def on_msg(room, msg, sender, is_group_chat, *args):
    return f"Message from {room}, {sender}: {msg}"


if __name__ == "__main__":
    bot.run(host="0.0.0.0", port=8081)
