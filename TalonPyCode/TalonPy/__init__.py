"""TalonPy.

Description goes here
"""

import logging
from .localhost import LocalHost
from .remotehost import RemoteHost
from .sectorcommandinterface import SectorCommandInterface
from .sectorcodebook import SectorCodebook
from .sweepstatistics import SweepStatistics
from .talon import Talon
from .boardfile import BoardFile
from .method import Method
from .methodindependent import MethodIndependent
from .methodindependentlow import MethodIndependent_low
from .mcsparser import MCS_PARSER

__all__ = [
    'LocalHost',
    'RemoteHost',
    'SectorCommandInterface',
    'SectorCodebook',
    'SweepStatistics',
    'Talon',
    'BoardFile',
    'Method',
    'MethodIndependent',
    'MethodIndependent_low',
    'MCS_PARSER'
]

log_defaults = {
    'log_format': '%(asctime)s %(levelname)-5s %(message)s',
    'log_datefmt': '%Y-%m-%d %H:%M:%S',
    'log_level': logging.INFO,
    'log_file_dir': '/var/log/'
}

# Configure the Log System
logging.basicConfig(
    format=log_defaults['log_format'],
    datefmt=log_defaults['log_datefmt'],
    level=log_defaults['log_level'])
