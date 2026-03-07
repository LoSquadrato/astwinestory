from enum import Enum

# Supported formats
class TweeFormat(Enum):
    SUGARCUBE = "SugarCube"


# Supported format version:
# add version to format after compatibility verification
SUPPORTED_FORMAT_VERSIONS = {
    "SugarCube" : [
        "2.37.3"
    ]
}