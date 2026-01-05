import os

class profiles:
    def __init__(self):
        self.profilesPath = os.path.abspath("profiles")
        self.mainProfile = os.path.join(self.profilesPath, "main")
        os.makedirs(self.mainProfile, exist_ok=True)

    def getPath(self):
        return self.mainProfile
    
Profiles = profiles()