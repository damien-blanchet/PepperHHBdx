#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import argparse
import sys
import time
import logging

import qi


class SandBox(object):
    def __init__(self, app):

        # Initialisation of qi framework and event detection.
        self.app = app
        self.app.start()
        session = self.app.session

        self.logger = logging.getLogger('SandBox')  # TODO : Fix the logger
        self.logger.info("Initialisation du main !")

        self.video_device = session.service('ALVideoDevice')
        self.face_detection = session.service('ALFaceDetection')
        self.memory = session.service('ALMemory')

        self.faceDetectionSubscriber = self.memory.subscriber("FaceDetected")
        self.id_face_detected = self.faceDetectionSubscriber.signal.connect(self.on_face_detected)

        self.face_detection_handle = self.face_detection.subscribe('SandBox', 200, 0)
        self.camera_handle = self.video_device.subscribeCamera('SandBox', 0, 1, 13, 15)

        self.width = 320
        self.height = 240
        self.x_rad_to_pix_ratio = self.width/0.9983
        self.y_rad_to_pix_ratio = self.height/0.7732

        self.run()

    def get_interest_zones(self):
        image = [[], [], []]
        result = self.video_device.getImageRemote(self.camera_handle)
        start_time = time.time()

        if result is None:
            print 'cannot capture.'
        elif result[6] is None:
            print 'no image data string.'
        else:
            # translate value to mat
            values = list(result[6])
            i = 0
            for x in range(result[0]):
                for y in range(result[1]):
                    if self.is_in_triangle((x, y), self.left_eye_pixels[0], self.left_eye_pixels[1],
                                           self.mouth_pixels[0]):
                        image[0].append(values[i + 0])
                        image[1].append(values[i + 1])
                        image[2].append(values[i + 2])
                        i += 3
        stop_time = time.time()
        print "Time taken: " + str(stop_time - start_time)
        return image

    def on_face_detected(self, value):
        face_info = value[1][0][1]
        left_eye = face_info[3]
        right_eye = face_info[4]
        mouth = face_info[8]
        # [left(x,y),right(x,y)]
        self.left_eye_pixels = [(-round(left_eye[4]*self.x_rad_to_pix_ratio)+self.width/2,
                            round(left_eye[5]*self.y_rad_to_pix_ratio)+self.height/2),
                           (-round(left_eye[2]*self.x_rad_to_pix_ratio)+self.width/2,
                            round(left_eye[3]*self.y_rad_to_pix_ratio)+self.height/2)]
        self.right_eye_pixels = [(-round(right_eye[2]*self.x_rad_to_pix_ratio)+self.width/2,
                             round(right_eye[3]*self.y_rad_to_pix_ratio)+self.height/2),
                            (-round(right_eye[4]*self.x_rad_to_pix_ratio)+self.width/2,
                             round(right_eye[5]*self.y_rad_to_pix_ratio)+self.height/2)]
        self.mouth_pixels = [(-round(mouth[0]*self.x_rad_to_pix_ratio)+self.width/2,
                         round(mouth[1]*self.y_rad_to_pix_ratio)+self.height/2),
                        (-round(mouth[2]*self.x_rad_to_pix_ratio)+self.width/2,
                         round(mouth[3]*self.y_rad_to_pix_ratio)+self.height/2)]

        image = self.get_interest_zones()
        print 'Done :'
        print len(image[0])
        print len(image[1])
        print len(image[2])

    # args : ((x,y),(x,y),(x,y))
    def scalar_product(self, test_point, first_point, second_point):
        return (test_point[0] - second_point[0]) * (first_point[1] - second_point[1]) \
               - (first_point[0] - second_point[0]) * (test_point[1] - second_point[1])

    def is_in_triangle(self, test_point, A, B, C):
        test_1 = self.scalar_product(test_point, A, B) > 0
        test_2 = self.scalar_product(test_point, B, C) > 0
        test_3 = self.scalar_product(test_point, C, A) > 0
        return (test_1 == test_2) and (test_2 == test_3)

    def run(self):
        """
        Main application loop. Waits for manual interruption.
        """
        self.logger.info("Starting Scheduler")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrupted by user, stopping Scheduler")
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
