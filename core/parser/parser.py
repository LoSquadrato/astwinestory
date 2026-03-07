'''
from dataclasses import dataclass
from itertools import count

@dataclass
class Parser:
    
    
    def __init__(self, format_def: FormatDefinition):
        self.format_def = format_def
        self._counter = count(1)  # parte da 1

    def _next_id(self) -> int:
        return next(self._counter)
    
  

# cambio formato da una story a un'altra
    def get_format(story : Story) -> Story:
        format = Story.format
        # a seconda dal formato scelgo il modulo del parser
        pass
'''