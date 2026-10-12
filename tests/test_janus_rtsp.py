import os
import tempfile
import unittest
from unittest import mock

from moonraker_obico import janus_config_builder
from moonraker_obico.webcam_stream import WebcamStreamer


class Webcam(object):
    def __init__(self, mode, h264_rtsp_url=None, is_primary_camera=True):
        self.streaming_params = dict(mode=mode)
        self.h264_rtsp_url = h264_rtsp_url
        self.is_primary_camera = is_primary_camera


def assign(webcams):
    streamer = WebcamStreamer.__new__(WebcamStreamer)
    streamer.webcams = webcams
    streamer.assign_janus_params()
    return webcams


class H264RtspTests(unittest.TestCase):

    def build(self, webcams):
        with tempfile.TemporaryDirectory() as etc:
            with mock.patch.object(janus_config_builder, 'RUNTIME_JANUS_ETC_DIR', etc):
                janus_config_builder.build_janus_plugin_streaming_jcfg(webcams)
                with open(os.path.join(etc, 'janus.plugin.streaming.jcfg')) as f:
                    return f.read()

    def test_rtsp_webcam_gets_stream_id_and_dataport(self):
        (cam,) = assign([Webcam('h264_rtsp', 'rtsp://cam:8554/mini')])
        self.assertEqual(cam.runtime['stream_id'], 1)
        self.assertIn('dataport', cam.runtime)
        self.assertNotIn('videoport', cam.runtime)

    def test_configured_url_is_used(self):
        cams = assign([Webcam('h264_rtsp', 'rtsp://cam:8554/mini')])
        jcfg = self.build(cams)
        self.assertIn('type = "rtsp"', jcfg)
        self.assertIn('url = "rtsp://cam:8554/mini"', jcfg)
        self.assertIn('dataport = {}'.format(cams[0].runtime['dataport']), jcfg)

    def test_legacy_rtsp_port_still_works(self):
        cams = assign([Webcam('h264_rtsp')])
        cams[0].streaming_params['rtsp_port'] = 8554
        self.assertIn('url = "rtsp://127.0.0.1:8554/stream.h264"', self.build(cams))

    def test_missing_url_raises(self):
        cams = assign([Webcam('h264_rtsp')])
        with self.assertRaises(Exception):
            self.build(cams)


if __name__ == '__main__':
    unittest.main()
