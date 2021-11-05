import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def closeexample(resp):
    if resp.event.message:
        print('Detected a message')
        bot.gateway.close()

bot.gateway.run(auto_reconnect=True)

bot.gateway.clear_commands() #run this if you want to clear commands
bot.gateway.reset_session() #run this if you want to clear collected session data from last connection
bot.gateway.run(auto_reconnect=True) #and now you can connect to the gateway server again
