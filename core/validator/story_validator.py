from core.ast.story import Story

class StoryValidator:

    @staticmethod
    def validate(data: dict) -> list[str]:
        errors = []

        if not data.get("ifid"):
            errors.append("Missing IFID")

        if not data.get("start"):
            errors.append("Missing start node")

        # altre regole...

        return errors