import logging
import os
import datetime as dt
import requests
import json

from reminder_bot import constants
from discord.ext import commands

from pathlib import Path

logger = logging.getLogger(__name__)
URL_BASE = 'https://clist.by/api/v1/contest/'
_CLIST_API_TIME_DIFFERENCE = 30 * 60



class ClistApiError(commands.CommandError):

    def __init__(self, message=None):
        super().__init__(message or 'Clist API error')


class ClientError(ClistApiError):

    def __init__(self):
        super().__init__('Error connecting to Clist API')


def _query_api():
    clist_token = os.getenv('CLIST_API_TOKEN')
    contests_start_time = dt.datetime.utcnow() - dt.timedelta(days=20)
    contests_start_time_string = contests_start_time.strftime(
        "%Y-%m-%dT%H%%3A%M%%3A%S")
    url = URL_BASE + '?limit=200&start__gte=' + \
        contests_start_time_string + '&' + clist_token

    try:
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ClistApiError
        return resp.json()['objects']
    except Exception as e:
        logger.error(f'Request to Clist API encountered error: {e!r}')
        raise ClientError from e