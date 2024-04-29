import argparse
import os, sys, json, time, traceback
from mm.config import ConfigParser
from mm.logging_utils import get_logger, make_logger, reset_logging
from mm.model_utils import registered_model_getters
from mm.interfaces import registered_interfaces
from mm.transformers import registered_transformers
import torch
import time, logging, asyncio

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

    # publish
    parser.add_argument(
        "-p",
        "--publish",
        help="Publish data to system, if True data is published, otherwise the step is skipped",
        required=False,
        default=False,
        action="store_true",
    )

    args = parser.parse_args()

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
        config = model_getter.get_config()
        config = initailize_config(config)
        logger.info(f"Configuration file obtained from model: {config}")
        logger.debug(f"Configuration: {config}")
    else:
        logger.info(f"Configuration file provided: {args.config}")
        config = initailize_config(args.config)

    # configure input and output interface transformers
    logger.debug("Configuring input and output interface transformers")
    logger.debug(f"Input transformer: {config.input_data_to_model.type}")
    logger.debug(f"Output transformer: {config.output_model_to_data.type}")

    # configure interfaces
    logger.debug("Configuring interfaces")
    logger.debug(f"In_interfaces: {config.input_data.get_method}")
    logger.debug(f"Out_interfaces: {config.output_data_to.put_method}")

    in_interface = registered_interfaces[config.input_data.get_method](
        config.input_data.config
    )
    out_interface = registered_interfaces[config.output_data_to.put_method](
        config.output_data_to.config
    )
    in_transformer = registered_transformers[config.input_data_to_model.type](
        config.input_data_to_model.config
    )
    out_transformer = registered_transformers[config.output_model_to_data.type](
        config.output_model_to_data.config
    )

    logger.info(f"Model: {args.model_name} version: {args.model_version} loaded")
    logger.info(f"Model type: {model_getter.model_type}")

    return (
        in_interface,
        out_interface,
        in_transformer,
        out_transformer,
        model_info,
        model_getter,
        args,
        config.deployment.type
    )


async def model_main(
    in_interface,
    out_interface,
    in_transformer,
    out_transformer,
    model,
    model_getter,
    args,
):
    """Main."""
    # monitor and send to transformer handle
    # reintialise logger to get the correct logger and clear any previous handlers
    print("model_main")

    logger = get_logger()
    logger.info("Starting model manager")

    stats_inference = []
    stats_input_transform = []
    stats_output_transform = []
    stats_put = []
    last_stat_report = time.time()

    try:
        in_interface.monitor(in_transformer.handler)
        logger.info("Monitoring input interface")

        # initialise variables using get
        for key in in_interface.variable_list:
            _, value = in_interface.get(key)
            # measure size of value in bytes

            in_transformer.handler(key, value)

        while True:
            if time.time() - last_stat_report > 1:
                stat_string = ""
                if len(stats_inference) > 0:
                    stat = sum(stats_inference) / len(stats_inference)
                    stat = stat * 1000
                    # display 2 decimal places
                    stat_temp = f" | Inference time: {stat:.2f} ms |"
                    spaces = 20 - len(stat_temp)
                    stat_string += stat_temp + " " * spaces

                if len(stats_input_transform) > 0:
                    stat = sum(stats_input_transform) / len(stats_input_transform)
                    stat = stat * 1000
                    stat_temp = f" Input transform time: {stat:.2f} ms |"
                    spaces = 20 - len(stat_temp)
                    stat_string += stat_temp + " " * spaces
                if len(stats_output_transform) > 0:
                    stat = sum(stats_output_transform) / len(stats_output_transform)
                    stat = stat * 1000
                    stat_temp = f" Output transform time: {stat:.2f} ms |"
                    spaces = 20 - len(stat_temp)
                    stat_string += stat_temp + " " * spaces

                if len(stats_put) > 0:
                    stat = sum(stats_put) / len(stats_put)
                    stat = stat * 1000
                    stat_temp = f" Put time: {stat:.2f} ms |"
                    spaces = 20 - len(stat_temp)
                    stat_string += stat_temp + " " * spaces

                if stat_string == "":
                    pass
                else:
                    logger.info(stat_string)
                    last_stat_report = time.time()
                    stats_inference = []
                    stats_input_transform = []
                    stats_output_transform = []
                    stats_put = []

            if in_transformer.updated:
                try:
                    stats_input_transform.append(in_transformer.handler_time)
                except:
                    logger.warning("No handler time available for stats")
                    stats_input_transform.append(0)
                # logger.debug("Input transformer updated")
                # logger.debug(
                #     f"Input transformer latest transformed: {in_transformer.latest_transformed}"
                # )

                # logger.debug("Evaluating model")

                # this part can maybe be handled by lume-model
                if model_getter.model_type == "torch":
                    latest_transformed = in_transformer.latest_transformed
                    for key in latest_transformed:
                        # convert to tensor
                        latest_transformed[key] = torch.tensor(
                            latest_transformed[key], dtype=torch.float32
                        )

                else:
                    latest_transformed = in_transformer.latest_transformed

                inference_start = time.time()
                output = model.evaluate(in_transformer.latest_transformed)
                inference_time = time.time() - inference_start
                stats_inference.append(inference_time)
                logger.debug(f"Output from model.evaluate: {output}")
                # print("=" * 20)
                # print("Output from model.evaluate: ")
                # print(output)
                # print("=" * 20)
                for key in output:
                    logger.debug(f"Output: {key}: {output[key]}")
                    out_transformer.handler(key, {"value": output[key]})

                if out_transformer.updated:
                    try:
                        stats_output_transform.append(out_transformer.handler_time)
                    except:
                        logger.warning("No handler time available for stats")
                        stats_output_transform.append(0)
                    time_start = time.time()

                    if os.environ["PUBLISH"] == "True":
                        logger.debug("Publishing data")
                        out_interface.put_many(out_transformer.latest_transformed)
                    else:
                        logger.debug(
                            "Not publishing data, to publish use -p or --publish"
                        )
                    out_transformer.updated = False

                    time_end = time.time()
                    stats_put.append(time_end - time_start)

                in_transformer.updated = False

                if args.one_shot:
                    logger.info("One shot mode, exiting")
                    break

            await asyncio.sleep(
                0.0001
            )  # makes the loop less cpu intensive 100% - > 15% cpu usage , more refactoring needed to make it more efficient

    except Exception as e:
        logger.error(f"Error monitoring: {traceback.format_exc()}")
        raise e
    finally:
        out_interface.close()
        in_interface.close()

        logger.info("Exiting")
        sys.exit(0)
