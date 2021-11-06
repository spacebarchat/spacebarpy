import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def helloworld1(resp):
    if resp.event.ready:
        user = bot.gateway.session.user
        print('Logged in as {}#{}'.format(user['username'], user['discriminator']))

@bot.gateway.command
def helloworld2(resp):
    if resp.event.message:
        print('Detected a message')
        bot.gateway.clear_commands()

bot.gateway.run(auto_reconnect=True)
