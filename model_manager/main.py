from mm.cli import model_main, setup
from mm.logging_utils import make_logger

logger = make_logger("model_manager")

# run as python python .\model_manager\main.py

# if __name__ == "__main__":
#     logger.critical("Starting model manager")
#     in_interface, out_interface, in_transformer, out_transformer, model = setup()
#     model_main(in_interface, out_interface, in_transformer, out_transformer, model)

# # run as module
# else:
logger.critical("Starting model manager")
in_interface, out_interface, in_transformer, out_transformer, model, getter, args = setup()
model_main(in_interface, out_interface, in_transformer, out_transformer, model,getter, args)
