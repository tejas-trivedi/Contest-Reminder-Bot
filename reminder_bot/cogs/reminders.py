import asyncio
import random
import functools
import json
import pickle
import logging
import time
import datetime as dt
from pathlib import Path
from recordtype import recordtype
import pytz
import copy

from collections import defaultdict
from collections import namedtuple

import discord
from discord.ext import commands
import os

from remind.util.rounds import Round
from remind.util import discord_common
from remind.util import paginator
from remind import constants
from remind.util import clist_api as clist

_CONTESTS_PER_PAGE = 5
_CONTEST_PAGINATE_WAIT_TIME = 5 * 60
_FINISHED_CONTESTS_LIMIT = 5
_CONTEST_REFRESH_PERIOD = 10 * 60  # seconds
_GUILD_SETTINGS_BACKUP_PERIOD = 6 * 60 * 60  # seconds

_PYTZ_TIMEZONES_GIST_URL = ('https://gist.github.com/heyalexej/'
                            '8bf688fd67d7199be4a1682b3eec7568')


class RemindersCogError(commands.CommandError):
    pass


def _contest_start_time_format(contest, tz):
    start = contest.start_time.replace(tzinfo=dt.timezone.utc).astimezone(tz)
    return f'{start.strftime("%d %b %y, %H:%M")} {tz}'


def _contest_duration_format(contest):
    duration_days, duration_hrs, duration_mins, _ = discord_common.time_format(
        contest.duration.total_seconds())
    duration = f'{duration_hrs}h {duration_mins}m'
    if duration_days > 0:
        duration = f'{duration_days}d ' + duration
    return duration


def _get_formatted_contest_desc(
        start,
        duration,
        url,
        max_duration_len):
    em = '\N{EN SPACE}'
    sq = '\N{WHITE SQUARE WITH UPPER RIGHT QUADRANT}'
    desc = (f'`{em}{start}{em}|'
            f'{em}{duration.rjust(max_duration_len, em)}{em}|'
            f'{em}`[`link {sq}`]({url} "Link to contest page")')
    return desc


def _get_embed_fields_from_contests(contests, localtimezone):
    infos = [(contest.name,
              _contest_start_time_format(contest,
                                         localtimezone),
              _contest_duration_format(contest),
              contest.url) for contest in contests]
    max_duration_len = max(len(duration) for _, _, duration, _ in infos)

    fields = []
    for name, start, duration, url in infos:
        value = _get_formatted_contest_desc(
            start, duration, url, max_duration_len)
        fields.append((name, value))
    return fields

