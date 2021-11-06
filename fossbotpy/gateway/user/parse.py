#parses response from gateway

class UserParse(object):
	@staticmethod
	def sessions_replace(response, session_id):
		importantdata = {}
		active_counter = {} #priority = 0
		all_counter = {} #priority = 1
		sessionid_counter = {} #priority = 2
		#sessions_replace is one of those undocumented events that have weird formatting. :(
		for session in response['d']:
			if session.get('active') == True:
				active_counter = session
				break; #no need to check anything else
			elif session.get('session_id') == 'all':
				all_counter = session
			elif session.get('session_id') == session_id:
				sessionid_counter = session
		#now start the processing
		if len(active_counter) > 0:
			importantdata['status'] = active_counter['status']
			importantdata['activities'] = {i['type']:i for i in active_counter['activities']}
			return importantdata
		elif len(all_counter) > 0:
			importantdata['status'] = all_counter['status']
			importantdata['activities'] = {j['type']:j for j in all_counter['activities']}
			return importantdata
		elif len(sessionid_counter) > 0:
			importantdata['status'] = sessionid_counter['status']
			importantdata['activities'] = {k['type']:k for k in sessionid_counter['activities']}
			return importantdata
		else:
			return {}
