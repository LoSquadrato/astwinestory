from enum import Enum
from dataclasses import dataclass

# Supported formats
# better use a dict?
@dataclass
class TweeFormat(Enum):
    SUGARCUBE = 1
    

    @classmethod
    def list(cls):
        return list(map(lambda c: c.name, cls))
    # print(TweeFormat.list())
'''
Python's Enum object has build-in enumerable.name and enumerable.value attributes for each member of an Enum.

an_enum = Enum('AnEnum', {'first': 1, 'second': 2})


[el.value for el in an_enum]
# returns: [1, 2]

[el.name for el in an_enum]
# returns: ['first', 'second']
Sidenode: Be careful with assert. If someone runs your script with python -O asserts will never fail.

To check if a value is part of an enum:

if 1 in [el.value for el in an_enum]:
    pass
'''
# Supported format version:
# add version to format after compatibility verification
SUPPORTED_FORMAT_VERSIONS = {
    "SugarCube" : [
        "2.37.3"
    ]
}


