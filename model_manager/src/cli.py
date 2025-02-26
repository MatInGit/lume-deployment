import argparse
import asyncio
import json
import logging
import os
import sys
import time
import traceback

import numpy as np
import torch
from model_manager.src.config import ConfigParser
from model_manager.src.interfaces import registered_interfaces
from model_manager.src.logging_utils import get_logger, make_logger
from model_manager.src.model_utils import registered_model_getters
from model_manager.src.transformers import registered_transformers
from model_manager.src.utils.messaging import (
    Message,
    MessageBroker,
    TransformerObserver,
    InterfaceObserver,
    ModelObserver,
)

from model_manager.src.utils.builder import Builder

from model_manager._version import __version__

logger = get_logger()

init_time = time.time()

# if file build-info exists, set the environment variables
if os.path.exists("build-info.json"):
    with open("build-info.json") as stream:
        data = json.load(stream)
    for key, value in data.items():
        os.environ[key] = value

print("=" * 120)
# print(f"Commit head: {os.environ['vcs-ref']}")
# print(f"Build time: {os.environ['build-date']}")
print(f"Version: {__version__}")
print("=" * 120 + "\n")


def initailize_config(config_path):
    """Initialize the configuration."""
    try:
        config_parser = ConfigParser(config_path)
        return config_parser.parse()
    except Exception as e:
        logger.error(f"Error initializing configuration: {e}")
        raise e


def get_model_getter(model_getter, config=None):
    """Get the model."""
    logger.debug(f"Getting model: {model_getter} with config: {config}")
    try:
        model_getter = registered_model_getters[model_getter](config)
        return model_getter
    except Exception as e:
        logger.error(f"Error getting model getter: {e}")
        raise e


def env_config(env_config):
    """Set the environment variables."""
    logger.debug(f"Setting environment variables from: {env_config}")
    try:
        # load json
        with open(env_config) as stream:
            data = json.load(stream)
        for key, value in data.items():
            os.environ[key] = value
    except Exception as e:
        logger.error(f"Error setting environment variables: {e}")
        raise e


def setup():
    """Setup the model manager."""
    parser = argparse.ArgumentParser(description="Model Manager CLI")

    # parser.add_argument(
    #     "-l",  # expects 3 arguments
    #     "--local",
    #     help="Local mode, run without mlflow",
    #     required=False,
    #     nargs=2,
    # )

    parser.add_argument(
        "-d",
        "--debug",
        help="Debug mode",
        required=False,
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "-c", "--config", help="Path to the configuration file", required=False
    )
    parser.add_argument(
        "-g",
        "--model_getter",
        help="Method to obtain the model",
        choices=["mlflow", "local"],
        default="mlflow",
    )
    # parser.add_argument(
    #     "-n",
    #     "--model_name",
    #     required=False,
    #     help="Name of the model to be loaded from mlflow",
    # )
    # parser.add_argument(
    #     "-v",
    #     "--model_version",
    #     help="Version of the model to be loaded from mlflow",
    # )
    parser.add_argument(
        "-r",
        "--reqirements",
        help="reqirements install only, if True requirements.txt is obtained from the model and installed, program then exits",
        required=False,
        default=False,
        action="store_true",
    )
    # env
    parser.add_argument(
        "-e",
        "--env",
        help="Path to the environment configuration file, json format",
        required=False,
    )

    parser.add_argument(
        "-o",
        "--one_shot",
        help="One shot mode, run once and exit, helpful for debugging",
        required=False,
        default=False,
        action="store_true",
    )

    # publish
    parser.add_argument(
        "-p",
        "--publish",
        help="Publish data to system, if True data is published, otherwise the step is skipped",
        required=False,
        default=False,
        action="store_true",
    )

    # version print and exit
    parser.add_argument(
        "-V",
        "--version",
        help="Print version and exit",
        required=False,
        default=False,
        action="store_true",
    )

    args = parser.parse_args()

    if args.version:
        os.environ["version"] = __version__
        print(f"Model Manager version: {os.environ['version']}")
        sys.exit(0)

    # change logger level
    if args.debug:
        print("Debug mode")
        logger = make_logger(level=logging.DEBUG)
        os.environ["DEBUG"] = "True"
    else:
        print("Info mode")
        logger = make_logger(level=logging.INFO)
        os.environ["DEBUG"] = "False"

    logger.info("Model Manager CLI")

    logger.debug(f"Arguments: {args}")

    if args.publish:
        logger.warning("Publishing data to system")
        os.environ["PUBLISH"] = "True"
    else:
        logger.warning("Not publishing data to system, to publish use -p or --publish")
        os.environ["PUBLISH"] = "False"

    # env useful when running in windows
    if args.env:
        env_config(args.env)

    # if args.local is not None:
    #     # model getter
    #     model_getter = get_model_getter(
    #         "local",
    #         {
    #             "model_path": args.local[0],
    #             "model_factory_class": args.local[1],
    #         },
    #     )
    # else:
    #     # model getter
    #     model_getter = get_model_getter(
    #         "mlflow",
    #         {
    #             "model_name": args.model_name,
    #             "model_version": args.model_version,
    #         },
        # )

    # requirements install and quit
    # if args.reqirements:
    #     deps = model_getter.get_requirements()
    #     for line in open(deps).readlines():
    #         logger.debug(f"Installing {line}")
    #         os.system(f"pip install {line}")
    #     logger.info("Requirements installed, exiting")
    #     sys.exit(0)

    # get model and config

    # model = model_getter.get_model()

    if not args.config:
        logger.info(
            "No configuration file provided, getting config from model artifacts"
        )
        # check if os.environ["MODEL_CONFIG_FILE"] exists
        if os.environ["MODEL_CONFIG_FILE"]:
            builder = Builder(args.config)
        else:
            raise Exception("No configuration file provided, this should be done via command -c line or environment variable MODEL_CONFIG_FILE")
    else:
        logger.info(f"Configuration file provided: {args.config}")
        builder = Builder(args.config)
    
    
    broker = builder.build()

    # in_interface = registered_interfaces[config.input_data.get_method](
    #     config.input_data.config
    # )
    # out_interface = registered_interfaces[config.output_data_to.put_method](
    #     config.output_data_to.config
    # )
    # in_transformer = registered_transformers[config.input_data_to_model.type](
    #     config.input_data_to_model.config
    # )
    # out_transformer = registered_transformers[config.output_model_to_data.type](
    #     config.output_model_to_data.config
    # )

    # # wrap in observer
    # in_interface_wrapped = InterfaceObserver(in_interface)
    # out_interface_wrapped = InterfaceObserver(out_interface)
    # in_transformer_wrapped = TransformerObserver(in_transformer)
    # out_transformer_wrapped = TransformerObserver(out_transformer)
    # model_wrapped = ModelObserver(model)

    # # add observers to message broker
    # broker = MessageBroker()
    # # default sequence
    # # in_interface -> in_transformer -> model -> out_transformer -> out_interface
    # # this will be specified in the config file or default to the above, not implemented as of yet
    # broker.attach(in_interface_wrapped, "update_trigger") # update_trigger is a topic that is used to trigger the update of the model
    # broker.attach(in_transformer_wrapped, "in_interface")
    # broker.attach(model_wrapped, "in_transformer")
    # broker.attach(out_transformer_wrapped, "model")
    # broker.attach(out_interface_wrapped, "out_transformer")
    

    # logger.debug("Model manager setup complete")
    # logger.debug(f"Broker: {broker}")
    # logger.debug(f"Observers attached: {broker._observers}")

    # logger.info(f"Model: {args.model_name} version: {args.model_version} loaded")
    # logger.info(f"Model type: {model_getter.model_type}")

    # logger.info(f"Model loaded in {time.time() - init_time} seconds")

    return (
        args,
        builder.config,
        broker,
    )


async def model_main(
    args,
    config,
    broker):
    """Main."""
    # monitor and send to transformer handle
    # reintialise logger to get the correct logger and clear any previous handlers
    # print("model_main")

    logger = get_logger()
    logger.info("Starting model manager")

    stats_inference = []
    stats_input_transform = []
    stats_output_transform = []
    stats_put = []
    last_stat_report = time.time()
    os.environ["PUBLISH"] = str(args.publish)
    try:
        if config.deployment.type == "continuous":
            time_start = time.time()
            while True:
                if time.time() - time_start > config.deployment.rate:
                    time_start = time.time()
                    broker.get_all()
                
                if len(broker.queue) > 0:
                    broker.parse_queue()
                    if args.one_shot:
                        logger.info("One shot mode, exiting")
                        break
                
                await asyncio.sleep(0.01)
    
        else:
            raise Exception("Deployment type not supported")
 
    except Exception as e:
        logger.error(f"Error monitoring: {traceback.format_exc()}")
        raise e
    finally:
        logger.info("Exiting")
        sys.exit(0)
