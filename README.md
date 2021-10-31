# fossbotpy      
<img width="100" src="https://raw.githubusercontent.com/fosscord/fosscord/master/assets/logo_big_transparent.png" />       

[![version](https://badge.fury.io/py/fossbotpy.svg)](https://badge.fury.io/py/fossbotpy) [![python versions](https://img.shields.io/badge/python-2.7%20%7C%203.5%20%7C%203.6%20%7C%203.7%20%7C%203.8%20%7C%203.9-green)](https://pypi.org/project/fossbotpy)      
A simple, easy to use, non-restrictive, synchronous Fosscord API Wrapper for Selfbots/Userbots written in Python.       
-using requests and websockets :)        
-based off of the discum library      

## Table of Contents
- [Key Features](#Key-features)
- [Installation](#Installation)
  - [Prerequisites](#libs-used-installed-automatically-using-above-methods)
- [Documentation](docs)
- [Contributing](#Contributing)
- [Example Usage](#Quick-example)
- [Links](#Links)
- [Checklist](#Checklist)
- [Contributing](#Contributing)
- [FAQ](#FAQ)

## Key features
- easy-to-use (make selfbots/userbots)
- easy-to-extend/edit (add api wrappers)
- readable (organized 😃 )
- mimics the client while giving you control
- on-event (gateway) capabilities
- [op14 and op8 member fetching](docs/using/fetchingGuildMembers.md)
- support for python 2.7

## Installation
Python 2.7 or higher required
```
# Linux/macOS
python3 -m pip install -U fossbotpy

# Windows
py -3 -m pip install -U fossbotpy
```

#### libs used
installed automatically using above methods     
- requests
- requests_toolbelt
- brotli
- websocket_client==0.59.0
- filetype
- ua-parser
- random\_user\_agent
- colorama

## Contributing
Contributions are welcome. You can submit issues, make pull requests, or suggest features.        
Please see the [contribution guidelines](contributing.md)

# Quick example
```python
import fossbotpy
token = 'token'
base_url = 'https://dev.fosscord.com/api/v9/'
bot = fossbotpy.Client(token=token, base_url=base_url, log={"console":True, "file":False})

bot.send_message("238323948859439", "Hello :)")

@bot.gateway.command
def helloworld(resp):
    if resp.event.ready:
        user = bot.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp.event.message:
        m = resp.parsed.auto()
        guild_id = m.get('guild_id') #dms do not have a guild_id
        channel_id = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        content = m['content']
        print("> guild {} channel {} | {}#{}: {}".format(guild_id, channel_id, username, discriminator, content))

bot.gateway.run()
```

# Links
[Documentation](docs)      
[More examples](examples)      
[Changelog](changelog.md)      
[Source](https://github.com/discordtehe/fossbotpy)      
[PyPi](https://pypi.org/project/fossbotpy)      

# Checklist
- [x] Sending basic text messages
- [X] Sending Images
- [x] Sending Embeds
- [X] Sending Requests (Friends etc)
- [X] Profile Editing (Name,Status,Avatar)
- [X] On-Message (and other on-anything gateway) capabilities
- [X] Getting guild members
- [X] camelCase -> snake_case
- [ ] add the rest of the api wraps
- [ ] Everything

## FAQ
Q: How to fix "\[SSL: CERTIFICATE_VERIFY_FAILED]" errors?      
A: https://stackoverflow.com/a/53310545/14776493       

Q: ```import _brotli ImportError: DLL load failed: The specified module could not be found.``` How to fix?       
A: https://github.com/google/brotli/issues/782        
     
Q: ```The owner of this website has banned your access based on your browser's signature...```. How to fix?        
A: This is because of your user agent (https://stackoverflow.com/a/24914742/14776493). Either try again or reinitialize your client with a new user agent.       