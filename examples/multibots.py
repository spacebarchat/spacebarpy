#this first part is preparation. All we're doing is appending bot objects to a list so that we can access them from 1 spot later.
#we're also adding some functions to the gateway command list of each bot. Since each bot obj is different, 
#we can pass in the bot object into the close_after_readySupp gateway function.
import fossbotpy

with open('tokenlist.txt') as f:
	tokenlist = f.read().splitlines()

def close_after_ready(resp, bot):
	if resp.event.ready:
		bot.gateway.close()

clients = []
for i in range(len(tokenlist)):
	if i==0:
		clients.append(fossbotpy.Client(token=tokenlist[0], base_url='https://dev.fosscord.com/api/v9/'))
		build_num = clients[0]._Client__super_properties['client_build_number']
	else:
		clients.append(fossbotpy.Client(token=tokenlist[i], base_url='https://dev.fosscord.com/api/v9/', build_num=build_num))
	clients[i].gateway.command({'function':close_after_ready, 'params':{'bot':clients[i]}}) #add close_after_ready to each bot

#now for the fun part
#we use threading to make it run fast. You can use multiprocessing or subprocess if you'd like to instead. This is just one implementation.
import threading

def gateway_runner(bot, result, index):
	bot.gateway.run()
	result[index] = bot.gateway.session.user

num_clients = len(clients)
threads = [None] * num_clients
results = [None] * num_clients

for i in range(num_clients):
	threads[i] = threading.Thread(target=gateway_runner, args=(clients[i] , results, i)) #https://stackoverflow.com/a/6894023/14776493
	threads[i].start()

#results is a list containing all the client data (bot.gateway.session.user stuff)
for i in results: 
	print(i)
