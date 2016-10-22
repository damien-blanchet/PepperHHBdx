#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import argparse
import sys
import time
import logging

import qi

from democall import DemoCall
from module import saveDatas, loadDatas, parse_RGB, parse_ICA_results, normalize_matrix, normalize_array, \
    frequencyExtract, filterFreq, animate
import matplotlib.pyplot as plt
from matplotlib.pyplot import ion

import matplotlib.animation as animation


class SandBox(object):
    def __init__(self, app):

        # Initialisation of qi framework and event detection.
        self.app = app
        self.app.start()
        session = self.app.session

        # Plot initialisation
        ion()
        self.start_time = time.time()
        self.fig = plt.figure()
        plt.axis([0, 10, 0, 100])
        self.fig.suptitle("Cardio-frequency")
        self.subplt = self.fig.add_subplot(1, 1, 1)
        self.line1, = self.subplt.plot([], [], 'b-')
        self.freq_record = [0] * 100
        self.time_record = [float(f) / 10 for f in range(100)]
        self.data_set = [[], [], []]
        self.data_history = []
        self.data_times = []
        self.logger = logging.getLogger('SandBox')  # TODO : Fix the logger
        self.logger.info("Initialisation du main !")

        self.video_device = session.service('ALVideoDevice')
        self.face_detection = session.service('ALFaceDetection')
        self.memory = session.service('ALMemory')

        self.faceDetectionSubscriber = self.memory.subscriber("FaceDetected")
        self.id_face_detected = self.faceDetectionSubscriber.signal.connect(self.on_face_detected)

        self.face_detection_handle = self.face_detection.subscribe('SandBox', 200, 0)
        self.camera_handle = self.video_device.subscribeCamera('SandBox', 0, 0, 13, 15)

        self.width = 160
        self.height = 120
        self.x_rad_to_pix_ratio = self.width / 0.9983
        self.y_rad_to_pix_ratio = self.height / 0.7732

        self.left_eye_pixels = None
        self.right_eye_pixels = None
        self.mouth_pixels = None

        ## uncomment to set "demo" mode
        # try:
        # raw_input("Presser entree pour demarrer la demo d'appel")
        # finally:
        # self.DemoCall = DemoCall(app)
        # self.DemoCall.raiseHRAnomaly(1)

        self.run()

    def get_interest_zones(self):
        image = [[], [], []]
        result = self.video_device.getImageRemote(self.camera_handle)
        # start_time = time.time()

        if result is None:
            print 'cannot capture.'
        elif result[6] is None:
            print 'no image data string.'
        else:
            # translate value to mat
            values = list(result[6])
            i = 0
            x_min = min(self.left_eye_pixels[0][0], self.left_eye_pixels[1][0], self.mouth_pixels[0][0])
            x_max = max(self.left_eye_pixels[0][0], self.left_eye_pixels[1][0], self.mouth_pixels[0][0])
            y_min = min(self.left_eye_pixels[0][1], self.left_eye_pixels[1][1], self.mouth_pixels[0][1])
            y_max = max(self.left_eye_pixels[0][1], self.left_eye_pixels[1][1], self.mouth_pixels[0][1])
            if not sum([x_min, x_max, y_min, y_max]) == 0:
                for x in range(x_min, x_max):
                    for y in range(y_min, y_max):
                        if self.is_in_triangle((x, y), self.left_eye_pixels[0], self.left_eye_pixels[1],
                                               self.mouth_pixels[0]):
                            image[0].append(values[i + 0])
                            image[1].append(values[i + 1])
                            image[2].append(values[i + 2])
                            i += 3
        return image

    def on_face_detected(self, value):
        if value:
            face_info = value[1][0][1]
            left_eye = face_info[3]
            right_eye = face_info[4]
            mouth = face_info[8]
            # [left(x,y),right(x,y)]
            self.left_eye_pixels = [(self.width - int(left_eye[4] * self.x_rad_to_pix_ratio + self.width / 2),
                                     int(left_eye[5] * self.y_rad_to_pix_ratio + self.height / 2)),
                                    (self.width - int(left_eye[2] * self.x_rad_to_pix_ratio + self.width / 2),
                                     int(left_eye[3] * self.y_rad_to_pix_ratio + self.height / 2))]
            self.right_eye_pixels = [(self.width - int(right_eye[2] * self.x_rad_to_pix_ratio + self.width / 2),
                                      int(right_eye[3] * self.y_rad_to_pix_ratio + self.height / 2)),
                                     (self.width - int(right_eye[4] * self.x_rad_to_pix_ratio + self.width / 2),
                                      int(right_eye[5] * self.y_rad_to_pix_ratio + self.height / 2))]
            self.mouth_pixels = [(self.width - int(mouth[0] * self.x_rad_to_pix_ratio + self.width / 2),
                                  int(mouth[1] * self.y_rad_to_pix_ratio + self.height / 2)),
                                 (self.width - int(mouth[2] * self.x_rad_to_pix_ratio + self.width / 2),
                                  int(mouth[3] * self.y_rad_to_pix_ratio + self.height / 2))]

    def add_image_to_data_set(self, image):
        self.data_set[0].append(sum(image[0]) / float(len(image[0])))
        self.data_set[1].append(sum(image[1]) / float(len(image[1])))
        self.data_set[2].append(sum(image[2]) / float(len(image[2])))
        self.data_times.append(time.time())
        print len(self.data_set[0])
        if len(self.data_set[0]) >= 50:
            print 'Analyzing'
            fftresult = parse_RGB(len(self.data_set[0]), self.data_set)
            freq = frequencyExtract(fftresult, 15)
            self.freq_record.append(freq)
            self.data_history.append(self.freq_record.pop(0))
            self.line1.set_ydata(self.freq_record)
            self.line1.set_xdata(self.time_record)
            self.fig.canvas.draw()
            plt.pause(0.01)
            self.data_set = [self.data_set[0][10:], self.data_set[1][10:], self.data_set[2][10:]]

    # args : ((x,y),(x,y),(x,y))
    def scalar_product(self, test_point, first_point, second_point):
        return (test_point[0] - second_point[0]) * (first_point[1] - second_point[1]) \
               - (first_point[0] - second_point[0]) * (test_point[1] - second_point[1])

    def is_in_triangle(self, test_point, A, B, C):
        test_1 = self.scalar_product(test_point, A, B) > 0
        test_2 = self.scalar_product(test_point, B, C) > 0
        test_3 = self.scalar_product(test_point, C, A) > 0
        return (test_1 == test_2) and (test_2 == test_3)

    def get_frame(self):
        print time.time()
        if self.mouth_pixels is not None:
            image = self.get_interest_zones()
            if image[0]:
                self.add_image_to_data_set(image)

    def run(self):
        """
        Main application loop. Waits for manual interruption.
        """
        self.logger.info("Starting Scheduler")
        get_frame_task = qi.PeriodicTask()
        get_frame_task.setCallback(self.get_frame)
        get_frame_task.compensateCallbackTime(True)
        get_frame_task.setUsPeriod(60000)
        get_frame_task.start(True)
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user, stopping Scheduler")
            get_frame_task.stop()
            self.video_device.unsubscribe(self.camera_handle)
            self.face_detection.unsubscribe('SandBox')
            sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ip", type=str, default="127.0.0.1",
                        help="Robot IP address. On robot or Local Naoqi: use '127.0.0.1'.")
    parser.add_argument("--port", type=int, default=9559,
                        help="Naoqi port number")

    args = parser.parse_args()

    try:
        # Initialize qi framework.
        connection_url = "tcp://" + args.ip + ":" + str(args.port)
        qi_app = qi.Application(["Scheduler", "--qi-url=" + connection_url])
    except RuntimeError:
        print(("Can't connect to Naoqi at ip \"" + args.ip + "\" on port " + str(
            args.port) + ".\n Please check your script arguments. Run with -h option for help."))
        sys.exit(1)

    my_app = SandBox(qi_app)

    my_app.run()
