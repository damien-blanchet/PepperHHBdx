#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import argparse
import sys
import time
import logging

import qi

from democall import DemoCall

class SandBox(object):
    def __init__(self, app):

        # Initialisation of qi framework and event detection.
        self.app = app
        self.app.start()
        session = self.app.session

        self.logger = logging.getLogger('SandBox')  # TODO : Fix the logger
        self.logger.info("Initialisation du main !")

        try:
            raw_input("Presser entree pour demarrer la demo d'appel")
        finally:
            self.DemoCall = DemoCall(app)
            self.DemoCall.raiseHRAnomaly(1)
        try:
            raw_input("Presser entree pour stopper la demo")
        finally:
            self.DemoCall.exit(0)

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
