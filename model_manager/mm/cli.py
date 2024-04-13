import argparse
import os, sys, json
from mm.config import ConfigParser
from mm.logging_utils import get_logger
from mm.model_utils import registered_model_getters
from mm.interfaces import registered_interfaces

logger = get_logger()


def initailize_config(config_path):
    """Initialize the configuration."""
    try:
        config_parser = ConfigParser(config_path)
        return config_parser.parse()
    except Exception as e:
        logger.error(f"Error initializing configuration: {e}")
        raise e


def get_model_getter(model_name, model_version, model_getter):
    """Get the model."""
    logger.debug(
        f"Getting model: {model_name} version: {model_version} using {model_getter}"
    )
    try:
        model_getter = registered_model_getters[model_getter](model_name, model_version)
        return model_getter
    except Exception as e:
        logger.error(f"Error getting model getter: {e}")
        raise e


def env_config(env_config):
    """Set the environment variables."""
    logger.debug(f"Setting environment variables from: {env_config}")
    try:
        # load json
        with open(env_config, "r") as stream:
            data = json.load(stream)
        for key, value in data.items():
            os.environ[key] = value
    except Exception as e:
        logger.error(f"Error setting environment variables: {e}")
        raise e


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="Model Manager CLI")
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
    parser.add_argument(
        "-n",
        "--model_name",
        help="Name of the model to be loaded from mlflow",
        required=True,
    )
    parser.add_argument(
        "-v",
        "--model_version",
        help="Version of the model to be loaded from mlflow",
        required=True,
    )
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

    args = parser.parse_args()

    logger.info("Model Manager CLI")

    logger.debug(f"Arguments: {args}")

    # env useful when running in windows
    if args.env:
        env_config(args.env)

    # model getter
    model_getter = get_model_getter(
        args.model_name, args.model_version, args.model_getter
    )

    # requirements install and quit
    if args.reqirements:
        deps = model_getter.get_requirements()
        for line in open(deps, "r").readlines():
            logger.debug(f"Installing {line}")
            os.system(f"pip install {line}")
        logger.info("Requirements installed, exiting")
        sys.exit(0)

    # get model and config

    model_info = model_getter.get_model()

    if not args.config:
        logger.info(
            "No configuration file provided, getting config from model artifacts"
        )
        # config = model_getter.get_config()
    else:
        logger.info(f"Configuration file provided: {args.config}")
        config = initailize_config(args.config)

    # configure input and output interface transformers
    logger.debug("Configuring input and output interface transformers")
    logger.debug(
        f"Input transformer: {config.input_data_to_model.input_to_model_transform}"
    )
    logger.debug(
        f"Output transformer: {config.output_model_to_data.output_model_to_output_transform}"
    )

    # configure interfaces
    logger.debug("Configuring interfaces")
    logger.debug(f"In_interfaces: {config.input_data.get_method}")
    logger.debug(f"Out_interfaces: {config.output_data_to.put_method}")

    def dummy_handler(name, data):
        logger.info(f"Handler: {name} data: {data}")
        print(f"Handler: {name} data: {data}")

    in_interface = registered_interfaces[config.input_data.get_method](
        config.input_data
    )
    in_interface.monitor(dummy_handler)
    # out_interface = registered_interfaces[config.output_data_to.put_method](
    #     config.output_data_to, dummy_handler
    # )

    logger.info(f"Model: {args.model_name} version: {args.model_version} loaded")
    logger.info(f"Model type: {model_getter.model_type}")
