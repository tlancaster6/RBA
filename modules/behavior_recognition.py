"""code for defining a relationship between object detection data and one or more behaviors of interest"""
import logging
import cv2
import pandas as pd

logger = logging.getLogger(__name__)


class BehaviorRecognizer:

    def __init__(self, config):
        logger.debug('Beginning BehaviorRecognizer initialization')
        self.config = config
        self.behavior_check_window = config.behavior_check_window
        logger.debug(f'behavior check window set to {self.behavior_check_window} seconds')
        self.min_individuals_roi = config.behavior_min_individuals_roi
        self.max_individuals_roi = config.behavior_max_individuals_roi
        logger.debug(f'min and max individuals in ROI to trigger occupancy condition set to '
                    f'{self.min_individuals_roi} and {self.max_individuals_roi}')
        self.min_fraction_for_notification = config.behavior_min_fraction_for_notification
        logger.debug(f'notification will trigger when {self.min_fraction_for_notification * 100}% of recent frames'
                    f'meet the occupancy condition')
        self.data_buffer = []
        logger.info('BehaviorRecognizer successfully initialized')

    def append_data(self, timestamp, occupancy, thumbnail):
        self.data_buffer.append((timestamp, occupancy, thumbnail))
        while (len(self.data_buffer) >= 2) and (self.calc_buffer_length_seconds() > self.behavior_check_window):
            self.data_buffer.pop(0)

    def calc_activity_fraction(self):
        data = pd.DataFrame([x[:2] for x in self.data_buffer], columns=['timestamp', 'occupancy'])
        data_slice = data.query('@self.min_individuals_roi <= occupancy <= @self.max_individuals_roi')
        return len(data_slice) / len(data)

    def check_for_behavior(self):
        activity_fraction = self.calc_activity_fraction()
        if activity_fraction >= self.min_fraction_for_notification:
            return True
        return False

    def thumbnails_to_mp4(self, output_path):
        fourcc = cv2.VideoWriter_fourcc('m', 'p', '4', 'v')
        fps = 1 // self.config.framegrab_interval
        height, width, _ = self.data_buffer[0][2].shape
        video = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
        for _, occupancy, thumbnail in self.data_buffer:
            cv2.putText(thumbnail, f'{occupancy}', (0, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_8)
            video.write(thumbnail)
        video.release()

    def calc_buffer_length_seconds(self):
        return self.data_buffer[-1][0] - self.data_buffer[0][0]

    def reset(self):
        self.data_buffer = []
