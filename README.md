# Bot to take current timetable and monitor updates in channels for Binom Capital School via edupage's API

### Python modules and libraries used: (not built-in)
- [MongoDB](https://www.mongodb.com/) - 4.4.6
- [Python](https://www.python.org/) - 3.7+
- [beanie](https://pypi.org/project/beanie) - 1.16.6
- [httpx](https://pypi.org/project/httpx) - 3.8.1

#### Note:
I wrote [BinomTT/site](https://github.com/BinomTT/site) which stores Edupage's timetables
In this bot I used my own site, instead of edupage.org

### Config setup:
- Rename `config.yml.example` to `config.yml`
- Set values for this keys: `bot_token`, `db_uri`, `db_name`, `channel_url`
- Set values for `admins` (it means list of Telegram users' ID, which will receive information if edupage.org will give incorrect responses)

### License:
[MIT](LICENSE.md)
