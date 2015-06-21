import logging

from _pushbank.constants import LOGGING_FORMAT

logging.basicConfig(format=LOGGING_FORMAT)
logger = logging.getLogger('pushbank')

