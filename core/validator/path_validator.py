import os
from core.parser.formats import TweeFormat

class ValidationError(Exception):
    # Custom exception for validation errors

    def __init__(self, message: str):   
        super().__init__(message)

    def __str__(self):
        return f"Validation error: {self.args[0]}!"


    

