"""
Observable pattern implementation for MVVM data binding
"""
from typing import Any, Callable, Dict, List
from functools import wraps


class Observable:
    """Base class for observable objects that can notify observers of property changes"""
    
    def __init__(self):
        self._observers: Dict[str, List[Callable]] = {}
        self._property_values: Dict[str, Any] = {}
    
    def add_observer(self, property_name: str, callback: Callable[[str, Any, Any], None]):
        """Add an observer for a specific property"""
        if property_name not in self._observers:
            self._observers[property_name] = []
        self._observers[property_name].append(callback)
    
    def remove_observer(self, property_name: str, callback: Callable):
        """Remove an observer for a specific property"""
        if property_name in self._observers:
            self._observers[property_name].remove(callback)
    
    def notify_observers(self, property_name: str, old_value: Any, new_value: Any):
        """Notify all observers of a property change"""
        if property_name in self._observers:
            for callback in self._observers[property_name]:
                callback(property_name, old_value, new_value)


class ObservableProperty:
    """Descriptor for creating observable properties"""
    
    def __init__(self, initial_value: Any = None):
        self.initial_value = initial_value
        self.name = None
    
    def __set_name__(self, owner, name):
        self.name = f"_{name}"
    
    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return getattr(obj, self.name, self.initial_value)
    
    def __set__(self, obj, value):
        old_value = getattr(obj, self.name, self.initial_value)
        setattr(obj, self.name, value)
        if hasattr(obj, 'notify_observers'):
            obj.notify_observers(self.name[1:], old_value, value)


class Command:
    """Command pattern implementation for UI actions"""
    
    def __init__(self, execute_func: Callable, can_execute_func: Callable = None):
        self.execute_func = execute_func
        self.can_execute_func = can_execute_func or (lambda: True)
    
    def execute(self, *args, **kwargs):
        if self.can_execute():
            return self.execute_func(*args, **kwargs)
    
    def can_execute(self) -> bool:
        return self.can_execute_func()
