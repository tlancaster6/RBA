"""code for collecting basic video data and storing it locally on the raspberry pi"""

import picamera
import numpy as np
import datetime
import cv2
import logging
logger = logging.getLogger(__name__)
from time import sleep


class DataCollector:

    def __init__(self, video_dir, picamera_kwargs=None):
        logger.debug('Beginning data collector initialization')
        self.picamera_kwargs = picamera_kwargs
        self.video_dir = video_dir
        self.video_dir.mkdir(exist_ok=True, parents=True)
        self.cam = self.init_camera(picamera_kwargs)
        self.resolution = self.cam.resolution
        logger.info('DataCollector successfully initialized')

    def init_camera(self, picamera_kwargs):
        if picamera_kwargs:
            cam = picamera.PiCamera(**picamera_kwargs)
        else:
            cam = picamera.PiCamera()
        logger.debug('camera initialized')
        return cam

    def generate_h264_path(self):
        iso_string = datetime.datetime.now().isoformat(timespec='seconds').replace(':', '_')
        return self.video_dir / f'{iso_string}.h264'

    def start_recording(self):
        if self.cam.closed:
            logger.debug('reinitializing camera from scratch')
            self.cam = self.init_camera(self.picamera_kwargs)
        self.cam.start_recording(str(self.generate_h264_path()))
        sleep(2)
        logger.info('recording started')

    def split_recording(self):
        self.cam.split_recording(str(self.generate_h264_path()))
        logger.info('recording split')

    def stop_recording(self):
        self.cam.stop_recording()
        logger.info('recording stopped')

    def capture_frame(self):
        image = np.zeros((self.resolution[1], self.resolution[0], 3), dtype=np.uint8)
        self.cam.capture(image, format='rgb', use_video_port=True)
        return image

    def shutdown(self):
        logger.debug('shutting down DataCollector')
        try:
            self.stop_recording()
            sleep(1)
        except picamera.PiCameraNotRecording:
            logger.debug('Could not stop recording because camera was not recording. Skipping.')
        self.cam.close()
        sleep(1)
        if not self.cam.closed:
            logger.warning('camera object may not have closed correctly. Expected self.cam.closed==True, got False')
        logger.info('DataCollector shutdown complete')


class MockDataCollector:

    def __init__(self, source_video, framegrab_interval):
        logger.debug('Beginning MockDataCollector initialization')
        self.source_video = source_video
        self.cap = cv2.VideoCapture(str(self.source_video))
        self.resolution = (int(self.cap.get(3)), int(self.cap.get(4)))
        self.framerate = int(self.cap.get(cv2.CAP_PROP_FPS))
        self.framestep = int(self.framerate * framegrab_interval)
        self.current_frame = 0
        logger.info('MockDataCollector successfully initialized')

    def capture_frame(self):
        ret, img = self.cap.read()
        self.current_frame += 1
        if not ret:
            self.cap.release()
            return False
        while self.current_frame % self.framestep:
            ret, img = self.cap.read()
            self.current_frame += 1
            if not ret:
                self.cap.release()
                return False
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    def shutdown(self):
        self.cap.release()

    def start_recording(self):
        pass

    def stop_recording(self):
        pass

    def init_camera(self):
        pass

    def generate_h264_path(self):
        pass

    def split_recording(self):
        pass