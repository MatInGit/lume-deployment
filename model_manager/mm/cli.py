import argparse
import os, sys, json, time, traceback
from mm.config import ConfigParser
from mm.logging_utils import get_logger, make_logger
from mm.model_utils import registered_model_getters
from mm.interfaces import registered_interfaces
from mm.transformers import registered_transformers
import torch
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


def setup():
    """Setup the model manager."""
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
    
    parser.add_argument(
        "-o",
        "--one_shot",
        help="One shot mode, run once and exit, helpful for debugging",
        required=False,
        default=False,
        action="store_true",
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

    in_interface = registered_interfaces[config.input_data.get_method](
        config.input_data
    )
    out_interface = registered_interfaces[config.output_data_to.put_method](
        config.output_data_to
    )
    in_transformer = registered_transformers[
        config.input_data_to_model.input_to_model_transform
    ](
        config.input_data_to_model.config["variables"],
        list(config.input_data_to_model.config["variables"].keys()),
    )
    out_transformer = registered_transformers[
        config.output_model_to_data.output_model_to_output_transform
    ](
        config.output_model_to_data.config["variables"],
        list(config.outputs_model.config["variables"].keys()),
    )

    logger.info(f"Model: {args.model_name} version: {args.model_version} loaded")
    logger.info(f"Model type: {model_getter.model_type}")

    return in_interface, out_interface, in_transformer, out_transformer, model_info, model_getter ,args


def model_main(in_interface, out_interface, in_transformer, out_transformer, model, model_getter,args):
    """Main."""
    # monitor and send to transformer handle
    # reintialise logger to get the correct logger and clear any previous handlers
    logger = make_logger("model_manager")
    
    try:
        in_interface.monitor(in_transformer.handler)
        logger.info("Monitoring input interface")
        while True:

            if in_transformer.updated:
                logger.debug("Input transformer updated")
                logger.debug(
                    f"Input transformer latest transformed: {in_transformer.latest_transformed}"
                )

                logger.debug("Evaluating model")
                
                # this part can maybe be handled by lume-model
                if model_getter.model_type == "torch":
                    latest_transformed = in_transformer.latest_transformed
                    for key in latest_transformed:
                        # convert to tensor
                        latest_transformed[key] = torch.tensor(latest_transformed[key], dtype=torch.float32)

                else:
                    latest_transformed = in_transformer.latest_transformed
                    
                output = model.evaluate(in_transformer.latest_transformed)
                logger.debug(f"Output from model.evaluate: {output}")
                # print("=" * 20)
                # print("Output from model.evaluate: ")
                # print(output)
                # print("=" * 20)

                for key in output:
                    logger.debug(f"Output: {key}: {output[key]}")
                    out_transformer.handler(key, {"value": output[key]})

                if out_transformer.updated:
                    out_interface.put_many(out_transformer.latest_transformed)
                    out_transformer.updated = False

                in_transformer.updated = False
                
                if args.one_shot:
                    logger.info("One shot mode, exiting")
                    break

    except Exception as e:
        logger.error(f"Error monitoring: {traceback.format_exc()}")
        raise e
    finally:
        out_interface.close()
        in_interface.close()

        logger.info("Exiting")
        sys.exit(0)
