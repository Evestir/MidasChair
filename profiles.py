import os

class profiles:
    def __init__(self):
        self.profilesPath = os.path.abspath("profiles")
        self.mainProfile = os.path.join(self.profilesPath, "main")
        self.secnProfile = os.path.join(self.profilesPath, "secn")
        os.makedirs(self.mainProfile, exist_ok=True)
        os.makedirs(self.secnProfile, exist_ok=True)

    def getPath(self):
        return self.mainProfile

    def getSecnPath(self):
        return self.secnProfile
    
Profiles = profiles()