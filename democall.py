#! /usr/bin/env python
# -*- encoding: UTF-8 -*-

import sys

import qi


class DemoCall(object):
    def __init__(self, app):	
	self.app = app
        session = self.app.session
         
        self.ALDialog = session.service("ALDialog")
        self.ALDialog.setLanguage("French")

        self.ALMemory = session.service("ALMemory")       
        
        topic_path = "/home/nao/restitution/democall_frf.top"
        # Loading the topic given by the user (absolute path is required)
        topf_path = topic_path.decode('utf-8')
        self.topic_name = self.ALDialog.loadTopic(topf_path.encode('utf-8'))
        
        # Activating the loaded topic
        self.ALDialog.activateTopic(self.topic_name)
    
        # Starting the dialog engine - we need to type an arbitrary string as the identifier
        # We subscribe only ONCE, regardless of the number of topics we have activated
        self.ALDialog.subscribe('DemoCallDialog')

        self.exit_service = self.ALMemory.subscriber("DemoCall/Done")
        self.exit_service.signal.connect(self.exit)
		
    def raiseHRAnomaly(self,value):
		self.ALMemory.raiseEvent("HR/anomaly",value)

    def exit(self, value):
        # stopping the dialog engine
        self.ALDialog.unsubscribe('DemoCallDialog')
        # Deactivating the topic
        self.ALDialog.deactivateTopic(self.topic_name)

        # now that the dialog engine is stopped and there are no more activated topics,
        # we can unload our topic and free the associated memory
        self.ALDialog.unloadTopic(self.topic_name)
        exit(0)
