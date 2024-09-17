"""code for automating data uploads via rclone"""
import subprocess as sp
import os
from pathlib import Path, PurePosixPath
import logging
logger = logging.getLogger(__name__)

class Uploader:

    def __init__(self, local_project_dir, cloud_data_dir=None, video_framerate=30):
        logger.debug('Beginning Uploader initialization')
        self.local_project_dir = Path(local_project_dir)
        if cloud_data_dir is None:
            self.attempt_uploads = False
            logger.debug('cloud_data_dir was "None", so uploads will not be attempted')
        else:
            self.attempt_uploads = True
            self.cloud_data_dir = PurePosixPath(cloud_data_dir)
            self.cloud_project_dir = self.cloud_data_dir / self.local_project_dir.name
            logger.debug(f'uploads will be sent to {self.cloud_project_dir}')
        self.framerate = video_framerate
        logger.info('Uploader successfully initialized')

    def convert_and_upload(self):
        self.convert_h264s_to_mp4s()
        if self.attempt_uploads:
            self.upload_project()

    def convert_h264s_to_mp4s(self):
        logger.debug('converting h264s to mp4s')
        local_video_dir = self.local_project_dir / 'Videos'
        h264_paths = local_video_dir.glob('*.h264')
        for h264_p in h264_paths:
            mp4_path = h264_p.with_suffix('.mp4')
            command = ['ffmpeg', '-analyzeduration', '100M', '-probesize', '100M', '-r',
                       str(self.framerate), '-i', h264_p, '-threads', '1', '-c:v', 'copy', '-r',
                       str(self.framerate), mp4_path]
            out = sp.run(command, capture_output=True, encoding='utf-8')
            if os.path.exists(mp4_path) and (os.path.getsize(mp4_path) > os.path.getsize(h264_p)):
                os.remove(h264_p)
            else:
                logger.warning(f'failed to convert {h264_p.name} with error {out.stderr}')
                if os.path.exists(mp4_path):
                    os.remove(mp4_path)
        logger.debug('conversion complete')

    def upload_project(self):
        logger.debug('initiating upload')
        local_video_dir = self.local_project_dir / 'Videos'
        cloud_video_dir = self.cloud_project_dir / 'Videos'
        logger.debug(f'moving {local_video_dir} to {cloud_video_dir} (Local copies will be deleted)')
        vid_move_cmd = ['rclone', 'move', str(local_video_dir), str(cloud_video_dir)]
        vid_move_out = sp.run(vid_move_cmd, capture_output=True, encoding='utf-8')
        if vid_move_out.stderr:
            logger.warning(f'moving videos to cloud may have failed: \n {vid_move_out.stderr}')
        logger.debug(f'copying remaining project files to cloud (local copies will be preserved)')
        copy_cmd = ['rclone', 'copy', str(self.local_project_dir), str(self.cloud_project_dir)]
        copy_out = sp.run(copy_cmd, capture_output=True, encoding='utf-8')
        if copy_out.stderr:
            logger.warning(f'copying project files to cloud may have failed: \n {copy_out.stderr}')
        logger.debug('upload complete')



