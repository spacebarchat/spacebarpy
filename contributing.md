# Contributing

Hello :wave: and thank you for contributing! :tada:

Before you contribute, please take a minute to review the contribution process
based on what you want to do.

## I got an error or I have a question

Great! We are happy to help. Before you ask your question, please check if your
question can be answered from the following 5 steps:
- [ ] The [project examples](https://gitlab.com/arandomnewaccount/fossbotpy/-/tree/main/examples)
- [ ] The [project FAQ](https://gitlab.com/arandomnewaccount/fossbotpy#faq)
- [ ] Search for your question in [old existing issues](https://gitlab.com/arandomnewaccount/fossbotpy/-/issues)
- [ ] If you encountered an error message, try googling the error message and see if you find an answer
- [ ] Check if the same issue exists if you uninstall the fossbotpy
library on your system (using `pip uninstall fossbotpy` or maybe
`pip3 uninstall fossbotpy`) and install the
[latest main branch](https://gitlab.com/arandomnewaccount/fossbotpy)
directly from GitHub by using `python -m pip install --user --upgrade git+https://gitlab.com/arandomnewaccount/fossbotpy.git`
(see [installation info](https://gitlab.com/arandomnewaccount/fossbotpy#installation))

If you did not get your question answered from these 5 steps, then please open a
new issue and ask your question! When you explain your problem, please:
- [ ] [Enable logging](https://gitlab.com/arandomnewaccount/fossbotpy/-/blob/main/docs/using/General.md#logging)
and include the log that you got in your answer. Don't forget to remove tokens and any personal information (your username, user id, etc etc).
- [ ] Add an explanation for what you are trying to accomplish. If you can
provide your code (or example code) in the issue, this helps a lot!

## I have a suggestion or idea

Great! Please make a new issue an explain your idea, but first do a quick search
in [old existing issues](https://gitlab.com/arandomnewaccount/fossbotpy/-/issues)
to see if someone already proposed the same idea.

## I want to contribute code
Note: for large contributions, create an issue before doing all that work to ask whether your pull request is likely to be accepted.

Great! Just follow the steps:
1. Clone the repository
   ```
   git clone https://gitlab.com/arandomnewaccount/fossbotpy.git
   cd fossbotpy
   ```
2. Edit the code
3. test the code (make sure it works using python versions 2.7-3.9)
6. [Create a pull request](https://help.github.com/en/articles/creating-a-pull-request)
   so that your changes can be integrated into fossbotpy

In your pull request (PR), please explain:
1. What is the problem with the current code
2. How your changes make it better
3. Provide some example code that can allow someone else to recreate the
problem with the current code and test your solution (if possible to recreate).

## I want to contribute documentation

Great! To edit the [project documentation](https://gitlab.com/arandomnewaccount/fossbotpy/-/tree/main/docs),
create a pull request (PR).

## ps
most of this was pulled from these sources:      
https://github.com/websocket-client/websocket-client/blob/master/CONTRIBUTING.md      
https://github.com/Earthcomputer/clientcommands#contributing     
and then edited as needed to apply to this project.
