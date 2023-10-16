import re
from dataclasses import dataclass
from enum import Enum
from threefive import Cue

class SCTE35Type(Enum):
    CUE = "EXT-X-CUE"
    DATERANGE = "EXT-X-DATERANGE"
    OATCLS = "EXT-OATCLS-SCTE35"
    ALL="ALL"
    CUSTOM="custom"

@dataclass
class SCTE35:
    type: SCTE35Type

@dataclass
class SCTE35_OUT(SCTE35):
    id: str
    duration: float
    binarydata: str
    decoded: str


    def __str__(self):
        if self.binarydata is None:
            return f"ID={self.id}, DURATION={self.duration}"
        if self.decoded is None:
            return f"ID={self.id}, DURATION={self.duration},BINARYDATA={self.binarydata}"
        return f"ID={self.id}, DURATION={self.duration},BINARYDATA={self.binarydata}\n{self.decoded}"


@dataclass
class SCTE35_DATERANGE(SCTE35):
    id: str
    duration: float
    planned_duration: float
    start_date: str
    binarydata: str
    decoded: str

    def __str__(self):
        if self.decoded is None:
            return f"ID={self.id}, DURATION={self.duration}, PLANNED_DURATION={self.planned_duration}, START_DATE={self.start_date}, BINARYDATA={self.binarydata}\n"
        else:
            return f"ID={self.id}, DURATION={self.duration}, PLANNED_DURATION={self.planned_duration}, START_DATE={self.start_date}, BINARYDATA={self.binarydata}\n{self.decoded}"

@dataclass
class SCTE35_OATCLS(SCTE35):
    id: str
    binarydata: str
    decoded: str

    def __str__(self):
        if self.decoded is None:
            return f"ID={self.id}, BINARYDATA={self.binarydata}\n"
        else:
            return f"ID={self.id}, BINARYDATA={self.binarydata}\n{self.decoded}"


@dataclass
class SCTE35_CUSTOM(SCTE35):
    line: str

    def __str__(self):
        return f"{self.line}"


def parse_scte_35_cue_out(line, decode):
    pattern = r'#EXT-X-CUE(-OUT)?(-CONT)?:\s*(.*?)(?=\n|$)'
    match = re.search(pattern, line)
    if match:
        cue = SCTE35_OUT(SCTE35Type.CUE, -1, None, None, None)
        attributes = []
        field_text = match.group(3)
        attributes_str = field_text.split(',')
        for attribute_str in attributes_str:
            split = attribute_str.replace('"', '').split('=')
            if (len(split) == 1):
                key = "DURATION"
                value = split[0]
            else:
                key = split[0]
                value =  split[1]

            if value.isdigit():
                value = float(value)
            if key.upper() == "BREAKID" or key == "ID":
                cue.id = value
            elif key.upper() == "DURATION":
                cue.duration = value
            elif key.upper() == "SCTE35":
                cue.binarydata = value
            if decode:
                try:
                    c = Cue(cue.binarydata)
                    c.decode()
                    cue.decoded = c.get_json()
                except:
                    cue.decoded = "Failed to decode binarydata"
        return cue


def parse_scte_35_daterange(line, decode):
    pattern = r'#EXT-X-DATERANGE:\s*(.*?)(?=\n|$)'
    match = re.search(pattern, line)
    if match:
        cue = SCTE35_DATERANGE(SCTE35Type.DATERANGE, -1, None, None, None, None, None)
        attributes = []
        field_text = match.group(1)
        attributes_str = field_text.split(',')
        for attribute_str in attributes_str:
            split = attribute_str.replace('"', '').split('=')
            key = split[0]
            value =  split[1]

            if value.isdigit():
                value = float(value)
            if key.upper() == "BREAKID" or key == "ID":
                key = "ID"
                cue.id = value
            elif key.upper() == "DURATION":
                cue.duration = value
            elif key.upper() == "PLANNED-DURATION":
                cue.planned_duration = value
            elif key.upper() == "SCTE35-OUT":
                cue.binarydata = value
            elif key.upper() == "START-DATE":
                cue.start_date = value
            if decode:
                try:
                    c = Cue(cue.binarydata)
                    c.decode()
                    cue.decoded = c.get_json()
                except:
                    cue.decoded = "Failed to decode binarydata"
        return cue


def parse_scte_35_oatcls(line, decode):
    pattern = r'#EXT-OATCLS-SCTE35:(.*)'
    match = re.search(pattern, line)
    if match:
        cue = SCTE35_OATCLS(SCTE35Type.OATCLS, -1, None, None)
        attributes = []
        field_text = match.group(1)
        attributes_str = field_text.split(',')
        for attribute_str in attributes_str:
            split = attribute_str.replace('"', '').split('=')
            if (len(split) == 1):
                key = "BINARYDATA"
                value = split[0]
            else:
                key = split[0]
                value =  split[1]

            if value.isdigit():
                value = float(value)
            if key.upper() == "BREAKID" or key == "ID":
                key = "ID"
                cue.id = value
            if key.upper() == "BINARYDATA":
                cue.binarydata = value
            if decode:
                try:
                    c = Cue(cue.binarydata)
                    c.decode()
                    cue.decoded = c.get_json()
                except:
                    cue.decoded = "Failed to decode binarydata"
        return cue

def parse_scte_35_custom(line, custom_match):
    if custom_match in line:
        return SCTE35_CUSTOM(SCTE35Type.CUSTOM, line)
