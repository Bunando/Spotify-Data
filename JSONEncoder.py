import json

class CompactListJSONEncoder(json.JSONEncoder):
    def iterencode(self, obj, _one_shot=False):
        if isinstance(obj, list):
            # Handle lists of dictionaries with proper indentation but no extra newlines between items
            if all(isinstance(el, dict) for el in obj):
                return '[\n' + ',\n'.join('  ' + self.encode(el) for el in obj) + '\n]'
            # For other lists, keep them compact on one line
            return '[' + ', '.join(self.encode(el) for el in obj) + ']'
        elif isinstance(obj, dict):
            # For dictionaries, ensure proper indentation for keys/values and closing braces
            items = ['"{}": {}'.format(k, self.encode(v)) for k, v in obj.items()]
            return '{\n' + ',\n'.join('    ' + item for item in items) + '\n  }'
        return super().iterencode(obj, _one_shot)