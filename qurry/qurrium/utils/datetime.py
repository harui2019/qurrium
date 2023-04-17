from datetime import datetime


def currentTime():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


class datetimeDict(dict[str, str]):
    
    def addOnly(self, eventName: str):
        self[eventName] = currentTime()
    
    def addSerial(self, eventName: str):
        repeatTimesPlusOne = 1
        for d in self:
            if d.startswith(eventName):
                repeatTimesPlusOne += 1
        eventNameWithTimes = f"{eventName}."+f"{repeatTimesPlusOne}".rjust(3, '0')
        self[eventNameWithTimes] = currentTime()