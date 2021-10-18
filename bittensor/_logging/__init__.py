""" Standardize logging for bittensor
"""
# The MIT License (MIT)
# Copyright © 2021 Yuma Rao

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the “Software”), to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of
# the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
# THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

import os
import sys

import argparse
import copy

from loguru import logger

import bittensor

logger = logger.opt(colors=True)

# Remove default sink.
try:
    logger.remove( 0 )
except Exception:
    pass

class logging:
    """ Standardize logging for bittensor
    """
    __has_been_inited__:bool = False
    __debug_on__:bool = False
    __trace_on__:bool = False
    __std_sink__:int = None
    __file_sink__:int = None

    def __new__(
            cls,
            config: 'bittensor.Config' = None,
            debug: bool = None,
            trace: bool = None,
            record_log: bool = None,
            logging_dir: str = None,
        ):

        cls.__has_been_inited__ = True

        if config == None: 
            config = logging.config()
        config = copy.deepcopy(config)
        config.logging.debug = debug if debug != None else config.logging.debug
        config.logging.trace = trace if trace != None else config.logging.trace
        config.logging.record_log = record_log if record_log != None else config.logging.record_log
        config.logging.logging_dir = logging_dir if logging_dir != None else config.logging.logging_dir

        # Remove default sink.
        try:
            logger.remove( 0 )
        except Exception:
            pass

        # Optionally Remove other sinks.
        if cls.__std_sink__ != None:
            logger.remove( cls.__std_sink__ )
        if cls.__file_sink__ != None:
            logger.remove( cls.__file_sink__ )

        # Add filtered sys.stdout.
        cls.__std_sink__ = logger.add (
            sys.stdout,
            filter = cls.log_filter,
            colorize = True,
            enqueue = True,
            backtrace = True,
            diagnose = True,
            format = cls.log_formatter
        )

        cls.set_debug(config.logging.debug)
        cls.set_trace(config.logging.trace)

        # ---- Setup logging to root ----
        if config.logging.record_log:
            filepath = config.logging.logging_dir + "/logs.log"
            cls.__file_sink__ = logger.add (
                filepath,
                filter = cls.log_save_filter,
                enqueue = True,
                backtrace = True,
                diagnose = True,
                format = cls.log_save_formatter,
                rotation="25 MB",
                retention="10 days"
            )
            logger.success('Set record log:'.ljust(20) + '<blue>{}</blue>', filepath)
        else: logger.success('Set record log:'.ljust(20) + '<red>OFF</red>')

    @classmethod
    def config(cls):
        """ Get config from the argument parser
            Return: bittensor.config object
        """
        parser = argparse.ArgumentParser()
        logging.add_args( parser )
        return bittensor.config( parser )

    @classmethod
    def add_args(cls, parser: argparse.ArgumentParser):
        """ Accept specific arguments fro parser
        """
        try:
            parser.add_argument('--logging.debug', action='store_true', help='''Turn on bittensor debugging information''', default = bittensor.defaults.logging.debug )
            parser.add_argument('--logging.trace', action='store_true', help='''Turn on bittensor trace level information''', default = bittensor.defaults.logging.trace )
            parser.add_argument('--logging.record_log', action='store_true', help='''Turns on logging to file.''', default = bittensor.defaults.logging.record_log )
            parser.add_argument('--logging.logging_dir', type=str, help='Logging default root directory.', default = bittensor.defaults.logging.logging_dir )
        except argparse.ArgumentError:
            # re-parsing arguments.
            pass

    @classmethod   
    def add_defaults(cls, defaults):
        """ Adds parser defaults to object from enviroment variables.
        """
        defaults.logging = bittensor.Config()
        defaults.logging.debug = os.getenv('BT_LOGGING_DEBUG') if os.getenv('BT_LOGGING_DEBUG') != None else False
        defaults.logging.trace = os.getenv('BT_LOGGING_TRACE') if os.getenv('BT_LOGGING_DEBUG') != None else False
        defaults.logging.record_log = os.getenv('BT_LOGGING_RECORD_LOG') if os.getenv('BT_LOGGING_RECORD_LOG') != None else False
        defaults.logging.logging_dir = os.getenv('BT_LOGGING_LOGGING_DIR') if os.getenv('BT_LOGGING_LOGGING_DIR') != None else '~/.bittensor/miners'

    @classmethod
    def check_config( cls, config: 'bittensor.Config' ):
        """ Check config
        """
        assert config.logging

    @classmethod
    def set_debug(cls, debug_on: bool = True ):
        """ Set debug for the specific cls class 
        """
        if not cls.__has_been_inited__:
            cls()
        cls.__debug_on__ = debug_on
        if debug_on: 
            logging.success( prefix = 'Set debug', sufix = '<green>ON</green>')
        else:  
            logging.success( prefix = 'Set debug', sufix = '<red>OFF</red>')

    @classmethod
    def set_trace(cls, debug_on: bool = True):
        """ Set trace back for the specific cls class 
        """
        if not cls.__has_been_inited__:
            cls()
        cls._trace_on__ = debug_on
        if debug_on: 
            logging.success( prefix = 'Set trace', sufix = '<green>ON</green>')
        else:  
            logging.success( prefix = 'Set trace', sufix = '<red>OFF</red>')

    @classmethod
    def log_filter(cls, record ):
        """ Filter out debug log if debug is not on
        """
        if cls.__debug_on__ or cls.__trace_on__:
            return True
        else:
            return record["level"].name != "DEBUG"

    @classmethod
    def log_save_filter(cls, record ):
        if cls.__debug_on__ or cls.__trace_on__:
            return True
        else:
            return record["level"].name != "DEBUG"

    @classmethod
    def log_formatter(cls, record):
        """ Log with different format according to record['extra']
        """
        extra = record['extra']
        if 'rpc' in extra:
            log_format = "<blue>{time:YYYY-MM-DD HH:mm:ss.SSS}</blue> | " + extra['code_str'] + " | {extra[prefix]} | {extra[direction]} | {extra[arrow]} | {extra[uid_str]} | {extra[inputs]} | {extra[call_time]} | {extra[key_str]} | {extra[rpc_message]} \n"
            return log_format
        if 'receptor' in extra:
            log_format = "<blue>{time:YYYY-MM-DD HH:mm:ss.SSS}</blue> | " + extra['action'] + " | uid:{extra[uid]} | {extra[ip_str]} | hotkey:{extra[hotkey]} | coldkey:{extra[coldkey]} \n"
            return log_format
        else:
            return "<blue>{time:YYYY-MM-DD HH:mm:ss.SSS}</blue> | <level>{level: ^16}</level> | {message}\n"
   
    @classmethod
    def log_save_formatter(cls, record):
        extra = record['extra']
        if 'rpc' in extra:
            log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | " + extra['code_str'] + " | {extra[prefix]} | {extra[direction]} | {extra[arrow]} | {extra[uid_str]} | {extra[inputs]} | {extra[call_time]} | {extra[key_str]} | {extra[rpc_message]} \n"
            return log_format
        if 'receptor' in extra:
            log_format = "{time:YYYY-MM-DD HH:mm:ss.SSS} | " + extra['action'] + " | uid:{extra[uid]} | {extra[ip_str]} | hotkey:{extra[hotkey]} | coldkey:{extra[coldkey]} \n"
            return log_format
        else:
            return "{time:YYYY-MM-DD HH:mm:ss.SSS} | <level>{level: ^16}</level> | {message}\n"

    @classmethod
    def rpc_log( cls, axon: bool, forward: bool, is_response: bool, code:int, call_time: float, pubkey: str, uid: int = None, inputs:list = None, outputs:list = None, message:str = ''):
        """ Debug logging for the communication between endpoints with axon/dendrite 
        """

        if axon:
            prefix = "Axon"
        else:
            prefix = "Dendrite"
        prefix = prefix.center(len('Dendrite'))

        if forward:
            direction = "Forward"
        else:
            direction = "Backward"
        direction = direction.center(len('Backward'))

        if is_response:
            arrow = "<---"
        else:
            arrow = "--->"
        
        key_str = "{}".format( pubkey )
        call_time_str = "{:.2f}s".format(call_time).center(6)

        if uid != None:
            uid_str = str(uid).center(5)
        else:
            uid_str = "-".center(5)

        code_color = bittensor.utils.codes.code_to_loguru_color( code )
        code_string = bittensor.utils.codes.code_to_string( code )
        code_string = code_string.center(16)
        code_str = "<" + code_color + ">" + code_string + "</" + code_color + ">"

        if is_response:
            inputs = str(list(outputs)) if outputs != None else '[x]'
        else:
            inputs = str(list(inputs)) if inputs != None else '[x]'
        inputs = inputs.center(15)

        rpc_message = message if message != None else 'None'
        logger.debug( 'rpc', rpc=True, prefix=prefix, direction=direction, arrow=arrow, call_time = call_time_str, uid_str=uid_str, key_str=key_str, code_str=code_str, inputs = inputs, rpc_message = rpc_message)


    @classmethod
    def create_receptor_log( cls, endpoint: 'bittensor.Endpoint' ):
        """ Debug logging for the connection between endpoints 
        """
        logger.debug( 'endpoint', receptor=True, action = '<green>' + 'Connect'.center(16) + '</green>', uid=str(endpoint.uid).center(4), hotkey=endpoint.hotkey, coldkey=endpoint.coldkey, ip_str=endpoint.ip_str().center(27) )

    @classmethod
    def update_receptor_log( cls, endpoint: 'bittensor.Endpoint' ):
        """ Debug logging for updating the connection with endpoint
        """
        logger.debug( 'endpoint', receptor=True, action = '<blue>' + 'Update'.center(16) + '</blue>', uid=str(endpoint.uid).center(4), hotkey=endpoint.hotkey,  coldkey=endpoint.coldkey, ip_str=endpoint.ip_str().center(27) )

    @classmethod
    def destroy_receptor_log( cls, endpoint: 'bittensor.Endpoint' ):
        """ Debug logging for destroying connection with endpoint
        """
        logger.debug( 'endpoint', receptor=True, action = '<red>' + 'Destroy'.center(16) + '</red>', uid=str(endpoint.uid).center(4), hotkey=endpoint.hotkey,  coldkey=endpoint.coldkey, ip_str=endpoint.ip_str().center(27) )

    @classmethod
    def success( cls, prefix:str, sufix:str ):
        """ Success logging 
        """
        if not cls.__has_been_inited__:
            cls()
        prefix = prefix + ":"
        prefix = prefix.ljust(20)
        log_msg = prefix + sufix
        logger.success( log_msg )

    @classmethod
    def warning( cls, prefix:str, sufix:str ):
        """ Warning logging
        """
        if not cls.__has_been_inited__:
            cls()
        prefix = prefix + ":"
        prefix = prefix.ljust(20)
        log_msg = prefix + sufix 
        logger.warning( log_msg )

    @classmethod
    def error( cls, prefix:str, sufix:str ):
        """ Error logging
        """
        if not cls.__has_been_inited__:
            cls()
        prefix = prefix + ":"
        prefix = prefix.ljust(20)
        log_msg = prefix + sufix 
        logger.error( log_msg )

    @classmethod
    def info( cls, prefix:str, sufix:str ):
        """ Info logging
        """
        if not cls.__has_been_inited__:
            cls()
        prefix = prefix + ":"
        prefix = prefix.ljust(20)
        log_msg = prefix + sufix
        logger.info( log_msg )
