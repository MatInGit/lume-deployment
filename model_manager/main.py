def main():
    from mm.cli import model_main, setup
    from mm.logging_utils import make_logger, reset_logging

    logger = make_logger("model_manager")
    logger.info("Starting model manager")

    (
        in_interface,
        out_interface,
        in_transformer,
        out_transformer,
        model,
        getter,
        args,
    ) = setup()
    print("resetting logging...")
    reset_logging()
    logger = make_logger("model_manager")

    model_main(
        in_interface,
        out_interface,
        in_transformer,
        out_transformer,
        model,
        getter,
        args,
    )


if __name__ == "__main__":
    main()
