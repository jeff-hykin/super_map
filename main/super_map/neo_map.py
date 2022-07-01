import json_fix

map_data_for = {}
map_default_for = {}
map_uninitilized_children_for = {}
parent_callbacks_for = {}
was_autogenerated = {}
untouched_maps = set()


class Options:
    def __init__(self, data=None, default=None, _auto_generated=False, _parent_callbacks=None):
        self.default  = default or (lambda key, self, *args: Object(
            Options(_auto_generated=True,_parent_callbacks=[self, key])
        ))
        self.data            = data
        self._auto_generated = _auto_generated
        self._parent_callbacks = _parent_callbacks or []

    
class Object:
    def __init__(self, options_or_dict=None, **kwargs):
        this = id(self)
        options = options_or_dict if isinstance(options_or_dict, Options         ) else Options()
        a_dict  = options_or_dict if isinstance(options_or_dict, (dict, Object)) else {}
        # a_dict  = to_dict(a_dict)
        a_dict.update(kwargs)
        
        if len(a_dict) == 0:
            untouched_maps.add(this)
        
        map_data_for[this]         = a_dict
        map_default_for[this]      = options.default
        parent_callbacks_for[this] = options._parent_callbacks
        was_autogenerated[this]    = options._auto_generated
        self.__class__ = ObjectClass

class ObjectClass(Object):
    # this is "more powerful" than __getattr__
    def __getattribute__(self, attribute):
        data = map_data_for[id(self)]
        if attribute in data:
            return data[attribute]
        else:
            try:
                return object.__getattribute__(self, attribute)
            except Exception as error:
                return self[attribute]
    
    def __setattr__(self, key, value):
        this = id(self)
        data             = map_data_for[this]
        untouched        = this in untouched_maps
        parent_callbacks = parent_callbacks_for[this]
        if untouched and len(parent_callbacks):
            for each_parent, each_key in parent_callbacks:
                each_parent[each_key] = self
                del map_uninitilized_children_for[each_parent][each_key]
                untouched_maps.delete(each_parent)
        untouched_maps.delete(self)
        data[key] = value
    
    def __setitem__(self, key, value):
        this = id(self)
        data             = map_data_for[this]
        untouched        = this in untouched_maps
        parent_callbacks = parent_callbacks_for[this]
        
        if untouched and len(parent_callbacks):
            for each_parent, each_key in parent_callbacks:
                each_parent[each_key] = self
                del map_uninitilized_children_for[each_parent][each_key]
                untouched_maps.delete(each_parent)
        untouched_maps.delete(self)
        data[key] = value
    
    def __getattr__(self, key):
        this = id(self)
        data                  = map_data_for[this]
        uninitilized_children = map_uninitilized_children_for[this]
        default_function      = map_default_for[this]
        
        if key in data:
            return data[key]
        else:
            if key not in uninitilized_children:
                uninitilized_children[key] = default_function(key, self)
            return uninitilized_children[key]
    
    def __getitem__(self, key):
        this = id(self)
        data                  = map_data_for[this]
        uninitilized_children = map_uninitilized_children_for[this]
        default_function      = map_default_for[this]
        
        if key in data:
            return data[key]
        else:
            if key not in uninitilized_children:
                uninitilized_children[key] = default_function(key, self)
            return uninitilized_children[key]
            
    def __len__(self):
        return len(map_data_for[id(self)])
    
    def __contains__(self, key):
        return key in map_data_for[id(self)]
    
    def __delattr__(self, key):
        this = id(self)
        data                  = map_data_for[this]
        uninitilized_children = map_uninitilized_children_for[this]
        
        if key in data:
            del data[key]
        if key in uninitilized_children:
            child_id = id(uninitilized_children[key])
            # detach self from the UninitilizedChild
            parent_callbacks_for[child_id] = [
                (each_parent, each_key)
                    for each_parent, each_key in parent_callbacks_for[child_id]
                    if each_key != key
            ]
            del uninitilized_children[key]
    
    def __delitem__(self, key):
        this = id(self)
        data                  = map_data_for[this]
        uninitilized_children = map_uninitilized_children_for[this]
        
        
        if key in data:
            del data[key]
        if key in uninitilized_children:
            child_id = id(uninitilized_children[key])
            # detach self from the UninitilizedChild
            parent_callbacks_for[child_id] = [
                (each_parent, each_key)
                    for each_parent, each_key in parent_callbacks_for[child_id]
                    if each_key != key
            ]
            del uninitilized_children[key]
        
    # the truthy value of map
    def __nonzero__(self):
        this = id(self)
        if was_autogenerated[this] and map_uninitilized_children[this]:
            return False
        else:
            return True
    
    def __iter__(self):
        return map_data_for[id(self)].items()
    
    def __reversed__(self):
        return reversed(map_data_for[id(self)].items())
    
    def __repr__(self):
        return self.__str__()
    
    def __str__(self):
        data = map_data_for[id(self)]
        if len(data) == 0:
            return "{}"
        return _stringify(data)
    
    def __eq__(self, other):
        this = id(self)
        data = map_data_for[this]
        return data == other
    
    def __add__(self, other):
        # this is what makes += work
        this = id(self)
        data = map_data_for[this]
        if id(self) in untouched_maps and was_autogenerated[this]:
            for each_parent, each_key in parent_callbacks_for[this]:
                each_parent[each_key] = other
                return other
        else:
            if isinstance(other, dict):
                data.update(other)
                return self
            elif isinstance(other, Object):
                data.update(to_dict(other))
                return self
            else:
                # TODO: should probably be an error
                pass
    
    def __json__(self):
        return map_data_for[id(self)]



def to_dict(obj):
    if isinstance(obj, Object):
        return map_data_for[id(obj)]
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, (tuple, list)):
        return {
            index: each
                for index, each in enumerate(obj)
        }
    if isinstance(obj, (set, frozenset)):
        return {
            each: True
                for each in obj
        }
    
def keys(map):
    return list(to_dict(map).keys())

def values(map):
    return list(to_dict(map).values())

def items(map):
    return list(to_dict(map).items())

def overwrite(map, *args):
    data = to_dict(map)
    for each in args:
        data.update(to_dict(each))
    return map

def merge(*args):
    return overwrite(Object(), *args)

def copy(map):
    new_map = Object()
    original_id = id(map)
    new_id      = id(new_map)
    
    # duplicate data
    map_data[new_id]                  = dict(map_data[original_id])
    map_default_for[new_id]           = map_default_for[original_id]
    map_uninitilized_children[new_id] = dict(map_uninitilized_children[original_id])
    if original_id in untouched_maps:
        untouched_maps.add(new_id)
    
    return new_map

def sort_keys(map):
    a_dict = to_dict(map)
    keys = sorted(list(a_dict.keys()))
    dict_copy = {}
    # save copy and remove
    for each_key in keys:
        dict_copy[each_key] = a_dict[each_key]
        del a_dict[each_key]
    # re-add in correct order
    for each_key in keys:
        a_dict[each_key] = dict_copy[each_key]
    return map

# TODO
# def sort_values(map):
#     pass

# TODO
# def recursive_merge(map):
#     pass


Object.to_dict   = to_dict
Object.keys      = keys
Object.values    = values
Object.items     = items
Object.overwrite = overwrite
Object.merge     = merge
Object.copy      = copy
Object.sort_keys = sort_keys

def _indent(string, by):
    indent_string = (" "*by)
    return indent_string + string.replace("\n", "\n"+indent_string)

def _stringify(value):
    onelineify_threshold = 50 # characters (of inner content)
    length = 0
    if isinstance(value, str):
        return f'"{value}"'
    elif isinstance(value, Object):
        if len(value) == 0:
            return "{}"
        items = value if isinstance(value, Object) else value.items()
        output = "{\n"
        for each_key, each_value in items:
            element_string = _stringify(each_key) + ": " + _stringify(each_value)
            length += len(element_string)+2
            output += _indent(element_string, by=4) + ", \n"
        output += "}"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, dict):
        if len(value) == 0:
            return "{}"
        items = value if isinstance(value, Object) else value.items()
        output = "{\n"
        for each_key, each_value in items:
            element_string = _stringify(each_key) + ": " + _stringify(each_value)
            length += len(element_string)+2
            output += _indent(element_string, by=4) + ", \n"
        output += "}"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, list):
        if len(value) == 0:
            return "[]"
        output = "[\n"
        for each_value in value:
            element_string = _stringify(each_value)
            length += len(element_string)+2
            output += _indent(element_string, by=4) + ", \n"
        output += "]"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, set):
        if len(value) == 0:
            return "set([])"
        output = "set([\n"
        for each_value in value:
            element_string = _stringify(each_value)
            length += len(element_string)+2
            output += _indent(element_string, by=4) + ", \n"
        output += "])"
        if length < onelineify_threshold:
            output = output.replace("\n    ","").replace("\n","")
        return output
    elif isinstance(value, tuple):
        if len(value) == 0:
            return "tuple()"
        output = "(\n"
        for each_value in value:
            element_string = _stringify(each_value)
            length += len(element_string)+2
            output += _indent(element_string, by=4) + ", \n"
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
