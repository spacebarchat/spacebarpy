Get Started
===========

Installing
----------

```
# Linux/macOS
python3 -m pip install -U fossbotpy

# Windows
py -3 -m pip install -U fossbotpy
```

Initializing your client
------------------------

``` python
import fossbotpy
bot = fossbotpy.Client(token="token", base_url="https://dev.fosscord.com/api/v9/")
```

### Parameters:

-   **email** (Optional[str])
-   **password** (Optional[str])
-   **secret** (Optional[str]) - the 2FA secret string
-   **code** (Optional[str]) - TOTP 6 digit code
-   **token** (Optional[str]) - if you'd like to use fossbotpy without auth, input an invalid token like "poop"
-   **remote\_auth** (Optional[bool/str]) - use remote authentication (scan qr code) to login. Set as filename if you'd like to set a specific file location for the qr code image. Defaults to True
-   **proxy\_host** (Optional[str]) - proxy host without http(s) part
-   **proxy\_port** (Optional[str])
-   **user\_agent** (Optional[str]) - defaults to "random", which then randomly generates a user agent
-   **locale** (Optional[str]) - defaults to "en-US"
-   **build\_num** (Optional[int]) - defaults to "request", which then requests the fosscord build number
-   **base\_url** (Optional[str]) - defaults to "https://dev.fosscord.com/api/v9/"
-   **log** (Optional[dict]) - defaults to {"console":True, "file":False}. The value of "file" can be set to a filename (which is created if it does not exist)

### Returns:

a fossbotpy.Client object

examples
--------

A simple example showing how to use the REST api wraps and how to interact with fosscord's gateway:

``` python
import fossbotpy
bot = fossbotpy.Client(token='token')

bot.sendMessage("238323948859439", "Hello :)")

@bot.gateway.command
def helloworld(resp):
    if resp.event.ready:
        user = bot.gateway.session.user
        print("Logged in as {}#{}".format(user['username'], user['discriminator']))
    if resp.event.message:
        m = resp.parsed.auto()
        guildID = m.get('guild_id')
        channelID = m['channel_id']
        username = m['author']['username']
        discriminator = m['author']['discriminator']
        content = m['content']
        print("> guild {} channel {} | {}#{}: {}".format(guildID, channelID, username, discriminator, content))

bot.gateway.run()
```

[more examples](https://gitlab.com/arandomnewaccount/fossbotpy/-/tree/main/examples)
