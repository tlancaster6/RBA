"""code for running light-weight object detection to locate animals and regions of interest (roi's)"""

import cv2
from pycoral.adapters import common
from pycoral.adapters import detect
from pycoral.utils.edgetpu import make_interpreter, run_inference
import logging
from time import perf_counter
logger = logging.getLogger(__name__)

class DetectorBase:

    def __init__(self, model_path, confidence_thresh=0.25):
        logger.debug(f'Beginning DetectorBase initialization for {model_path.name}')
        self.confidence_thresh = confidence_thresh
        logger.debug(f'confidence threshold set to {confidence_thresh}')
        self.interpreter = make_interpreter(str(model_path))
        self.interpreter.allocate_tensors()
        logger.debug(f'interpreter initialized and tensors allocated')
        self.input_size = common.input_size(self.interpreter)
        logger.info(f'DetectorBase successfully initialized for {model_path.name}')

    def detect(self, img):
        scale = (self.input_size[1] / img.shape[1], self.input_size[0] / img.shape[0])
        img = cv2.resize(img, self.input_size)
        run_inference(self.interpreter, img.tobytes())
        dets = detect.get_objects(self.interpreter, self.confidence_thresh, scale)
        return sorted(dets, reverse=True, key=lambda x: x.score)




