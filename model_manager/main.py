def main():
    from mm.cli import model_main, setup
    from mm.logging_utils import make_logger, reset_logging
    import os, logging, asyncio

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
        dep_type,
    ) = setup()
    logger.info(f"Model deployed with type: {dep_type}")
    print("resetting logging...")
    reset_logging()

    if os.environ.get("DEBUG") == "True":
        logger = make_logger("model_manager", level=logging.DEBUG)
    else:
        logger = make_logger("model_manager")
        
    if dep_type == "continuous":    
        asyncio.run(
            model_main(
                in_interface,
                out_interface,
                in_transformer,
                out_transformer,
                model,
                getter,
                args,
            )
        )
    elif dep_type == "batch":
        raise NotImplementedError("Batch mode not implemented")

if __name__ == "__main__":
    main()
