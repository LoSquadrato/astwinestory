from dataclasses import dataclass 

@dataclass 
class ValidationResult: 
    errors: list[str] 
    warnings: list[str] 
    
    @property 
    def is_valid(self) -> bool: 
        return not self.errors
    
class StoryValidator: 
    @staticmethod 
    def validate_structure(data: dict) -> list[str]: 
        errors = [] 
        if not data.get("ifid"): 
            errors.append("Missing IFID") 
        if not data.get("start"): 
            errors.append("Missing start node") 
        if not data.get("format"): 
            errors.append("Missing format") 
            return errors 
        
    @staticmethod   
    def validate_semantics(data: dict) -> tuple[list[str], list[str]]: 
        errors = [] 
        warnings = [] # IFID UUID check 
        if "ifid" in data: 
            try: 
                uuid.UUID(data["ifid"]) 
            except Exception: 
                errors.append("Invalid IFID (must be valid UUID)") 
    # Format enum check 
            try: 
                StoryFormat(data["format"]) 
            except Exception: 
                errors.append(f"Unsupported format '{data.get('format')}'") 
    # Format-version check 
            fmt = data.get("format") 
            version = data.get("format-version") 
            
            if fmt in SUPPORTED_FORMAT_VERSIONS: 
                if version not in SUPPORTED_FORMAT_VERSIONS[fmt]: 
                    warnings.append( 
                        f"Format-version '{version}' not officially supported for '{fmt}'" 
                    ) 
            
            return errors, warnings 
        
    @classmethod 
    def validate(cls, data: dict) -> ValidationResult: 
        errors = [] 
        warnings = [] 
        errors += cls.validate_structure(data) 
        sem_errors, sem_warnings = cls.validate_semantics(data) 
        errors += sem_errors 
        warnings += sem_warnings 
        return ValidationResult(errors, warnings)