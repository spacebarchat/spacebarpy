import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

@bot.gateway.command
def example(resp):
    if resp.raw['t'] == 'MESSAGE_CREATE': #if you want to play with the raw response
        print('Detected a message')
        bot.gateway.removeCommand(example) #this works because bot.gateway.command returns the inputted function after adding the function to the command list

bot.gateway.run(auto_reconnect=True)
