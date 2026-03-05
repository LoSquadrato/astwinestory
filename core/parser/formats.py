from enum import Enum

# Supported formats
class TweeFormat(Enum):
    SUGARCUBE = "SugarCube"


# Supported format version:
# add version to format after compatibility verification
SUPPORTED_FORMAT_VERSION = {
    "Sugarcube" : [
        "2.37.3"
    ]
}