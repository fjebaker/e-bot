# e Discord Bot

<p align="center">
<a href="https://github.com/dustpancake/e-bot/actions/workflows/tests.yml"><img alt="tests" src="https://github.com/dustpancake/e-bot/actions/workflows/tests.yml/badge.svg?branch=master&event=push"></a>
<a href="https://github.com/dustpancake/e-bot/actions/workflows/docs.yml"><img src="https://github.com/dustpancake/e-bot/actions/workflows/docs.yml/badge.svg?branch=master&event=push" alt="docs"></a>
<a href="https://github.com/dustpancake/e-bot/pull/"><img alt="pull requests" src="https://img.shields.io/github/issues-pr/dustpancake/e-bot.svg"></a>
</p>


*A(nother) discord bot.*


## Overview
EBot is a discord bot for playing games and hosting gimmicks on your server. The games are inspired by popular party games, and currently features:

- *E Lash* : write clever and/or funny answers to silly prompts
- *E Cards* : functionally similar to Cards-against-Humanity but with custom prompts

## Setup
At the moment there is no way to invite this bot to your server unless you are hosting it yourself. For an overview, see [here for creating your own bot api keys](https://dustpancake.github.io/dust-notes/discord/making-bots-python.html#using-the-developer-portal-to-create-a-bot).

First clone
```bash
git clone https://github.com/dustpancake/e-bot && cd e-bot
```
Export your API key
```bash
export DISCORD_TOKEN="PASTE-KEY-HERE"
```

Then install dependencies and run. There are several methods for accomplishing this: 

### Using `pipenv`
```bash
pipenv install
pipenv run python src
```

### Using `pip`
```bash
pip install -r requirement.txt
python src
```