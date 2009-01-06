import noc.sa.script

class Script(noc.sa.script.Script):
    name="Audiocodes.Mediant2000.get_config"
    def execute(self):
        if self.access_profile.scheme in [self.TELNET,self.SSH]:
            self.cli("conf")
            config=self.cli("cf get")
        elif self.access_profile.scheme==self.HTTP:
            config=self.http.get("/FS/BOARD.ini")
        else:
            raise Exception("Unsupported access scheme")
        return self.cleaned_config(config)
