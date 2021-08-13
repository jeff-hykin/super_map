def indent(string, by):
    indent_string = (" "*by)
    return indent_string + string.replace("\n", "\n"+indent_string)

def stringify(value):
    onelineify_threshold = 50 # characters (of inner content)
    length = 0
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, dict):
        if len(value) == 0:
            return "{}"
        items = value if isinstance(value, Map) else value.items()
        output = "{\n"
        for each_key, each_value in items:
            element_string = stringify(each_key) + ": " + stringify(each_value)
            length += len(element_string)+2
            output += indent(element_string, by=4) + ", \n"
        output += "}"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, list):
        if len(value) == 0:
            return "[]"
        output = "[\n"
        for each_value in value:
            element_string = stringify(each_value)
            length += len(element_string)+2
            output += indent(element_string, by=4) + ", \n"
        output += "]"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, set):
        if len(value) == 0:
            return "set([])"
        output = "set([\n"
        for each_value in value:
            element_string = stringify(each_value)
            length += len(element_string)+2
            output += indent(element_string, by=4) + ", \n"
        output += "])"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, tuple):
        if len(value) == 0:
            return "tuple()"
        output = "(\n"
        for each_value in value:
            element_string = stringify(each_value)
            length += len(element_string)+2
            output += indent(element_string, by=4) + ", \n"
        output += ")"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    else:
        try:
            debug_string = value.__repr__()
        except Exception as error:
            from io import StringIO
            import builtins
            string_stream = StringIO()
            builtins.print(*args, **kwargs, file=string_stream)
            debug_string = string_stream.getvalue()
        
        # TODO: handle "<slot wrapper '__repr__' of 'object' objects>"
        if debug_string.startswith("<class") and hasattr(value, "__name__"):
            return value.__name__
        if debug_string.startswith("<function <lambda>"):
            return "(lambda)"
        if debug_string.startswith("<function") and hasattr(value, "__name__"):
            return value.__name__
        if debug_string.startswith("<module") and hasattr(value, "__name__"):
            _, *file_path, _, _ = debug_string.split(" ")[-1]
            file_path = "".join(file_path)
            return f"module(name='{value.__name__}', path='{file_path}')"
        
        space_split = debug_string.split(" ")
        if len(space_split) >= 4 and debug_string[0] == "<" and debug_string[-1] == ">":
            
            if space_split[-1].startswith("0x") and space_split[-1] == "at":
                _, *name_pieces = space_split[0]
                *parts, name = "".join(name_pieces).split(".")
                parts_str = ".".join(parts)
                return f'{name}(from="{parts_str}")'
        
        return debug_string

class Map():
    class SecretKey:
        pass

    class AutoGenerated(SecretKey):
        pass

    class Untouched(SecretKey):
        pass

    class ParentCallbacks(SecretKey):
        pass

    class UninitilizedChildren(SecretKey):
        pass

    class Keys(SecretKey):
        pass

    class Values(SecretKey):
        pass
    
    class Merge(SecretKey):
        pass
    
    class Default(SecretKey):
        pass
    
    class Dict(SecretKey):
        pass
        
    def __init__(self, *args, **kwargs):
        super(Map, self).__init__()
        secrets = args[1] if len(args) > 1 and args[0] == Map.SecretKey else {}
        secrets[Map.Untouched] = len(kwargs) == 0
        secrets[Map.UninitilizedChildren] = {}
        secrets[Map.Default] = lambda key, *args: Map(Map.SecretKey, {Map.AutoGenerated:True, Map.ParentCallbacks: [ (self, key) ], })
        super().__setattr__("d", ({}, secrets))
        data, secrets = super().__getattribute__("d")
        data.update(kwargs)
    
    # this is "more powerful" than __getattr__
    def __getattribute__(self, attribute):
        data, secrets = super().__getattribute__("d")
        if attribute == '__dict__':
            return data
        # if its not like __this__ then use the dict directly
        elif len(attribute) < 5 or not (attribute[0:2] == '__' and attribute[-2:len(attribute)] == "__"):
            return self[attribute]
        else:
            return object.__getattribute__(self, attribute)
    
    def __setattr__(self, key, value):
        data, secrets = super().__getattribute__("d")
        if secrets[Map.Untouched] and Map.ParentCallbacks in secrets:
            for each_parent, each_key in secrets[Map.ParentCallbacks]:
                each_parent[each_key] = self
                del each_parent[Map.UninitilizedChildren][each_key]
                each_parent[Map.SecretKey][Map.Untouched] = False
        secrets[Map.Untouched] = False
        data[key] = value
    
    def __setitem__(self, key, value):
        # FUTURE: have key be super-hashed, use ID's for anything that can't be yaml-serialized
        #         difficulty of implementation will be doing that^ without screwing up .keys()
        data, secrets = super().__getattribute__("d")
        if secrets[Map.Untouched] and Map.ParentCallbacks in secrets:
            for each_parent, each_key in secrets[Map.ParentCallbacks]:
                each_parent[each_key] = self
                del each_parent[Map.UninitilizedChildren][each_key]
                each_parent[Map.SecretKey][Map.Untouched] = False
        secrets[Map.Untouched] = False
        data[key] = value
    
    def __getattr__(self, key):
        data, secrets = super().__getattribute__("d")
        if key in data:
            return data[key]
        else:
            if key not in secrets[Map.UninitilizedChildren]:
                secrets[Map.UninitilizedChildren][key] = secrets[Map.Default](key)
            return secrets[Map.UninitilizedChildren][key]
    
    def __getitem__(self, key):
        data, secrets = super().__getattribute__("d")
        if key == Map.Keys:
            return data.keys()
        if key == Map.Values:
            return data.values()
        if key == Map.Dict:
            return data
        if key == Map.Merge:
            return lambda *args: [ data.update(each) for each in args ]
        if key in Map.SecretKey.__subclasses__():
            return secrets[key]
        if key == Map.SecretKey:
            return secrets
        if key in data:
            return data[key]
        else:
            if key not in secrets[Map.UninitilizedChildren]:
                secrets[Map.UninitilizedChildren][key] = secrets[Map.Default](key)
            return secrets[Map.UninitilizedChildren][key]
    
    def __len__(self):
        data, secrets = super().__getattribute__("d")
        return len(data)
    
    def __contains__(self, key):
        data, secrets = super().__getattribute__("d")
        return key in data
    
    def __delattr__(self, key):
        data, secrets = super().__getattribute__("d")
        if key in data:
            del data[key]
        if key in secrets[Map.UninitilizedChildren]:
            # detach self from the UninitilizedChild
            secrets[Map.UninitilizedChildren][key][Map.ParentCallbacks] = [
                (each_parent, each_key)
                    for each_parent, each_key in secrets[Map.UninitilizedChildren][key][Map.ParentCallbacks] 
                    if each_key != key
            ]
            del secrets[Map.UninitilizedChildren][key]
    
    def __delitem__(self, key):
        data, secrets = super().__getattribute__("d")
        if key in data:
            del data[key]
        if key in secrets[Map.UninitilizedChildren]:
            # detach self from the UninitilizedChild
            secrets[Map.UninitilizedChildren][key][Map.ParentCallbacks] = [
                (each_parent, each_key)
                    for each_parent, each_key in secrets[Map.UninitilizedChildren][key][Map.ParentCallbacks] 
                    if each_key != key
            ]
            del secrets[Map.UninitilizedChildren][key]
        
    # the return value of if Map():
    def __nonzero__(self):
        data, secrets = super().__getattribute__("d")
        if secrets[Map.AutoGenerated] and secrets[Map.UninitilizedChildren]:
            return False
        else:
            return True
    
    def __iter__(self):
        data, secrets = super().__getattribute__("d")
        return (each for each in data.items())
    
    def __reversed__(self):
        data, secrets = super().__getattribute__("d")
        return (each for each in reversed(data.items()))
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        data, secrets = super().__getattribute__("d")
        if len(data) == 0:
            return "{}"
        return stringify(data)
    
    def __eq__(self, other):
        data, secrets = super().__getattribute__("d")
        return data == other
    
    def __add__(self, other):
        data, secrets = super().__getattribute__("d")
        if secrets[Map.Untouched] and secrets[Map.AutoGenerated]:
            for each_parent, each_key in secrets[Map.ParentCallbacks]:
                each_parent[each_key] = other
                return other
        else:
            if isinstance(other, dict):
                data.update(other)
                return self
            # TODO: should probably be an error

class LazyDict(dict):
    def __init__(self, *args, **kwargs):
        super(LazyDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
    
    def __getitem__(self, key):
        return self.__dict__.get(key, None)
        
    def __delitem__(self, key):
        try:
            del self.__dict__[key]
        except Exception as error:
            pass
    
    def __str__(self):
        if len(self.__dict__) == 0:
            return "{}"
        return stringify(self.__dict__)
    
    def __repr__(self):
        return self.__str__()