import fossbotpy
bot = fossbotpy.Client(token='token', base_url='https://dev.fosscord.com/api/v9/')

#search guild members aka opcode 8 aka replacement for bot.getGuildMember()

#EXAMPLE 1: query member search in guild(s)
@bot.gateway.command
def test(resp):
    if resp.event.ready:
        bot.gateway.query_guild_members(['guild_id'], 'a', limit=100, keep='all')
    if resp.event.guild_members_chunk and bot.gateway.finished_guild_search(['guild_id'], 'a'):
        bot.gateway.close()

bot.gateway.run()

print(bot.gateway.guild_member_searches['guild_id']['queries']['a']) #user IDs of results
print(bot.gateway.session.guild('guild_id').members) #member data
bot.gateway.clear_commands()

#EXAMPLE 2: search for user_id(s) in guild(s)
@bot.gateway.command
def test(resp):
    if resp.event.ready:
        bot.gateway.check_guild_members(['guild_id'], ['user_id1', 'user_id2'], keep='all')
    if resp.event.guild_members_chunk and bot.gateway.finished_guild_search(['guild_id'], user_ids=['user_id1', 'user_id2']):
        bot.gateway.close()

bot.gateway.run()

print(bot.gateway.guild_member_searches['guild_id']['ids']) #user IDs of results
print(bot.gateway.session.guild('guild_id').members) #member data
bot.gateway.clear_commands()

#EXAMPLE 3: opcode 8 brute forcer
#not entirely random. Optimized quite a bit.

import time
import re

allchars = [' ', '!', '"', '#', '$', '%', '&', "'", '(', ')', '*', '+', ',', '-', '.', '/', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ':', ';', '<', '=', '>', '?', '@', '[', ']', '^', '_', '`', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z', '{', '|', '}', '~']
bot.gateway.guild_member_searches = {}
bot.gateway.reset_members_on_session_reconnect = False #member list brute forcing can take a while

class Queries:
    q_list = ['!'] #query list

class MemberFetchingScore:
    def __init__(self, per_request_expectation, per_second_expectation):
        self.per_request_expectation = per_request_expectation #expected # of members per request
        self.per_second_expectation = per_second_expectation #expected # of members per second
        self.effectiveness = 0
        self.efficiency = 0
        self.completeness = 0
    #percentage of requests returning back expected # of members
    def calculate_effectiveness(self, guild_id):
        self.effectiveness = 100*(len(bot.gateway.session.guild(guild_id).members)/len(bot.gateway.guild_member_searches[guild_id]['queries']))/self.per_request_expectation
    #percentage of expected members fetched per second
    def calculate_efficiency(self, guild_id, start_time):
        total_time = time.time() - start_time
        self.efficiency = 100*(len(bot.gateway.session.guild(guild_id).members)/total_time)/self.per_second_expectation
    #percentage of members fetched over total members in server
    def calculate_completeness(self, guild_id):
        self.completeness = 100*(len(bot.gateway.session.guild(guild_id).members)/bot.gateway.session.guild(guild_id).member_count)
    #average of measures, 0<=score<=100
    def get_score(self):
        return (self.effectiveness+self.efficiency+self.completeness)/3

s = MemberFetchingScore(100, 100)

def calculate_option(guild_id, action): #action == 'append' or 'replace'
    if action == 'append':
        last_user_i_ds = bot.gateway.guild_member_searches[guild_id]['queries'][''.join(Queries.q_list)]
        data = [bot.gateway.session.guild(guild_id).members[i] for i in bot.gateway.session.guild(guild_id).members if i in last_user_i_ds]
        last_name = sorted(set([re.sub(' +', ' ', j['nick'].lower()) if (j.get('nick') and re.sub(' +', ' ', j.get('nick').lower()).startswith(''.join(Queries.q_list))) else re.sub(' +', ' ', j['username'].lower()) for j in data]))[-1]
        try:
            option = last_name[len(Queries.q_list)]
            return option
        except IndexError:
            return None
    elif action == 'replace':
        if Queries.q_list[-1] in allchars:
            options = allchars[allchars.index(Queries.q_list[-1])+1:]
            if ' ' in options and (len(Queries.q_list)==1 or (len(Queries.q_list)>1 and Queries.q_list[-2]==' ')): #cannot start with a space and cannot have duplicate spaces
                options.remove(' ')
            return options
        else:
            return None

def find_replaceable_index(guild_id):
    for i in range(len(Queries.q_list)-2, -1, -1): #assume that the last index is not changable
        if Queries.q_list[i] != '~':
            return i
    return None

def brute_force_test(resp, guild_id, wait):
    if resp.event.ready:
        s.start_time = time.time()
        bot.gateway.query_guild_members([guild_id], query=''.join(Queries.q_list), limit=100, keep='all')
    elif resp.event.guild_members_chunk:
        remove = False
        if len(bot.gateway.guild_member_searches[guild_id]['queries'][''.join(Queries.q_list)]) == 100: #append
            append_option = calculate_option(guild_id, 'append')
            if append_option:
                Queries.q_list.append(append_option)
            else:
                remove = True
        else: #if <100 results returned, replace
            replace_options = calculate_option(guild_id, 'replace')
            if replace_options:
                Queries.q_list[-1] = replace_options[0]
            else:
                remove = True
        if remove: #if no replace options, find first replaceable index & replace it
            if len(Queries.q_list) == 1: #reached end of possibilities
                bot.gateway.remove_command({'function': brute_force_test, 'params':{'guild_id':guild_id, 'wait':wait}})
                s.calculate_efficiency(guild_id, s.start_time)
                print('efficiency: '+repr(s.efficiency)+'%')
                s.calculate_completeness(guild_id)
                print('completeness: '+repr(s.completeness)+'%')
                print('score: '+repr(s.get_score()))
                bot.gateway.close()
            else:
                replaceable_ind = find_replaceable_index(guild_id)
                if replaceable_ind != None:
                    Queries.q_list = Queries.q_list[:replaceable_ind+1]
                    replace_options = calculate_option(guild_id, 'replace')
                    Queries.q_list[-1] = replace_options[0]
                else:
                    bot.gateway.remove_command({'function': brute_force_test, 'params':{'guild_id':guild_id, 'wait':wait}})
                    s.calculate_efficiency(guild_id, s.start_time)
                    print('efficiency: '+repr(s.efficiency)+'%')
                    s.calculate_completeness(guild_id)
                    print('completeness: '+repr(s.completeness)+'%')
                    print('score: '+repr(s.get_score()))
                    bot.gateway.close()
        if wait: time.sleep(wait)
        print('next query: '+''.join(Queries.q_list))
        print('members fetched so far: '+repr(len(bot.gateway.session.guild(guild_id).members)))
        s.calculate_effectiveness(guild_id)
        print('effectiveness: '+repr(s.effectiveness)+'%')
        bot.gateway.query_guild_members([guild_id], query=''.join(Queries.q_list), limit=100, keep='all')


guild_id = ''
wait = 1
bot.gateway.command({'function': brute_force_test, 'params':{'guild_id':guild_id, 'wait':wait}})
bot.gateway.run()
