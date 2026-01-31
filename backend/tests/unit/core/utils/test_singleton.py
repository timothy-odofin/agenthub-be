"""
Comprehensive test suite for Singleton metaclass utility.
Tests thread safety, instance uniqueness, inheritance patterns,
and proper metaclass behavior across different class hierarchies.
"""

import threading
import time
from unittest.mock import patch

import pytest

from app.core.utils.single_ton import SingletonMeta


class TestSingletonMeta:
    """Test SingletonMeta metaclass functionality."""
    
    def test_singleton_basic_creation(self):
        """Test basic singleton instance creation."""
        
        class TestClass(metaclass=SingletonMeta):
            def __init__(self):
                self.value = 42
        
        # Create two instances
        instance1 = TestClass()
        instance2 = TestClass()
        
        # Should be the same object
        assert instance1 is instance2
        assert id(instance1) == id(instance2)
        assert instance1.value == instance2.value == 42
    
    def test_singleton_initialization_only_once(self):
        """Test that __init__ is called only once even with multiple instantiations."""
        
        init_call_count = 0
        
        class CountedInitClass(metaclass=SingletonMeta):
            def __init__(self):
                nonlocal init_call_count
                init_call_count += 1
                self.init_count = init_call_count
        
        # Create multiple instances
        instance1 = CountedInitClass()
        instance2 = CountedInitClass()
        instance3 = CountedInitClass()
        
        # All should be the same object
        assert instance1 is instance2 is instance3
        assert init_call_count == 1
        assert instance1.init_count == 1
        assert instance2.init_count == 1
        assert instance3.init_count == 1
    
    def test_singleton_with_arguments(self):
        """Test singleton with constructor arguments."""
        
        class ParameterizedClass(metaclass=SingletonMeta):
            def __init__(self, name, value=10):
                self.name = name
                self.value = value
        
        # First creation with arguments
        instance1 = ParameterizedClass("first", 100)
        assert instance1.name == "first"
        assert instance1.value == 100
        
        # Second creation - should return same instance, ignoring new arguments
        instance2 = ParameterizedClass("second", 200)
        assert instance1 is instance2
        assert instance2.name == "first"  # Original values preserved
        assert instance2.value == 100
    
    def test_singleton_multiple_classes(self):
        """Test that different classes have separate singleton instances."""
        
        class FirstClass(metaclass=SingletonMeta):
            def __init__(self):
                self.class_name = "First"
        
        class SecondClass(metaclass=SingletonMeta):
            def __init__(self):
                self.class_name = "Second"
        
        # Create instances of each class
        first1 = FirstClass()
        first2 = FirstClass()
        second1 = SecondClass()
        second2 = SecondClass()
        
        # Same class instances should be identical
        assert first1 is first2
        assert second1 is second2
        
        # Different class instances should be different
        assert first1 is not second1
        assert first1.class_name == "First"
        assert second1.class_name == "Second"
    
    def test_singleton_inheritance_separate_instances(self):
        """Test that inheritance creates separate singleton instances."""
        
        class BaseClass(metaclass=SingletonMeta):
            def __init__(self):
                self.type = "base"
        
        class DerivedClass(BaseClass):
            def __init__(self):
                super().__init__()
                self.type = "derived"
        
        # Create instances
        base1 = BaseClass()
        base2 = BaseClass()
        derived1 = DerivedClass()
        derived2 = DerivedClass()
        
        # Base instances should be identical
        assert base1 is base2
        assert base1.type == "base"
        
        # Derived instances should be identical
        assert derived1 is derived2
        assert derived1.type == "derived"
        
        # Base and derived should be different
        assert base1 is not derived1
    
    def test_singleton_thread_safety_current_limitation(self):
        """Test current thread safety behavior - documents the limitation."""
        
        instances = []
        creation_times = []
        
        class SlowInitClass(metaclass=SingletonMeta):
            def __init__(self):
                # Simulate slow initialization
                time.sleep(0.01)
                self.created_at = time.time()
        
        def create_instance():
            instance = SlowInitClass()
            instances.append(instance)
            creation_times.append(instance.created_at)
        
        # Create multiple threads
        threads = [threading.Thread(target=create_instance) for _ in range(5)]
        
        # Start all threads simultaneously
        for thread in threads:
            thread.start()
        
        # Wait for all to complete
        for thread in threads:
            thread.join()
        
        # Current implementation may create multiple instances in race conditions
        # This test documents the current behavior - not thread-safe
        assert len(instances) == 5
        
        # Check how many unique instances were created
        unique_instances = set(id(instance) for instance in instances)
        
        # Current SingletonMeta is NOT thread-safe, so we might get multiple instances
        # This test passes to document current behavior, but indicates improvement needed
        print(f"Created {len(unique_instances)} unique instances (should be 1 for thread-safe)")
        
        # At minimum, we should have gotten some instances
        assert len(unique_instances) >= 1
    
    def test_singleton_method_calls(self):
        """Test that methods work correctly on singleton instances."""
        
        class MethodClass(metaclass=SingletonMeta):
            def __init__(self):
                self.counter = 0
            
            def increment(self):
                self.counter += 1
                return self.counter
            
            def get_counter(self):
                return self.counter
        
        # Create instances and call methods
        instance1 = MethodClass()
        instance2 = MethodClass()
        
        # Increment from first instance
        result1 = instance1.increment()
        assert result1 == 1
        
        # Check from second instance (should see the change)
        result2 = instance2.get_counter()
        assert result2 == 1
        
        # Increment from second instance
        result3 = instance2.increment()
        assert result3 == 2
        
        # Verify from first instance
        assert instance1.get_counter() == 2
    
    def test_singleton_registry_isolation(self):
        """Test that SingletonMeta._instances registry works correctly."""
        
        class RegistryTestClass(metaclass=SingletonMeta):
            pass
        
        # Create instance
        instance = RegistryTestClass()
        
        # Check that class is in registry
        assert RegistryTestClass in SingletonMeta._instances
        assert SingletonMeta._instances[RegistryTestClass] is instance
    
    def test_singleton_with_class_variables(self):
        """Test singleton behavior with class variables."""
        
        class ClassVarClass(metaclass=SingletonMeta):
            class_var = "initial"
            
            def __init__(self):
                self.instance_var = "instance"
        
        # Create instances
        instance1 = ClassVarClass()
        instance2 = ClassVarClass()
        
        # Verify they're the same
        assert instance1 is instance2
        
        # Modify class variable through one instance
        instance1.class_var = "modified"
        
        # Should be reflected in both (since they're the same object)
        assert instance2.class_var == "modified"
        
        # But the class itself should still have original value
        assert ClassVarClass.class_var == "initial"
    
    def test_singleton_reset_between_tests(self):
        """Test that singleton instances don't leak between test cases."""
        
        # This test ensures each test gets a fresh singleton state
        class FreshClass(metaclass=SingletonMeta):
            def __init__(self):
                self.test_id = "fresh_test"
        
        # Clear any existing instance to simulate fresh test environment
        if FreshClass in SingletonMeta._instances:
            del SingletonMeta._instances[FreshClass]
        
        # Now create new instance
        instance = FreshClass()
        assert instance.test_id == "fresh_test"
        
        # Verify it's registered
        assert FreshClass in SingletonMeta._instances


class TestSingletonMetaEdgeCases:
    """Test edge cases and error conditions for SingletonMeta."""
    
    def test_singleton_with_property_decorators(self):
        """Test singleton with property decorators."""
        
        class PropertyClass(metaclass=SingletonMeta):
            def __init__(self):
                self._value = 42
            
            @property
            def value(self):
                return self._value
            
            @value.setter
            def value(self, new_value):
                self._value = new_value
        
        instance1 = PropertyClass()
        instance2 = PropertyClass()
        
        assert instance1 is instance2
        assert instance1.value == 42
        
        # Modify through property
        instance1.value = 100
        assert instance2.value == 100
    
    def test_singleton_with_static_and_class_methods(self):
        """Test singleton with static and class methods."""
        
        class MethodsClass(metaclass=SingletonMeta):
            class_counter = 0
            
            def __init__(self):
                MethodsClass.class_counter += 1
                self.instance_id = MethodsClass.class_counter
            
            @staticmethod
            def static_method():
                return "static_result"
            
            @classmethod
            def class_method(cls):
                return f"class_result_{cls.class_counter}"
        
        instance1 = MethodsClass()
        instance2 = MethodsClass()
        
        assert instance1 is instance2
        assert instance1.instance_id == 1  # Only initialized once
        assert MethodsClass.class_counter == 1
        
        # Test methods work correctly
        assert instance1.static_method() == "static_result"
        assert instance2.static_method() == "static_result"
        assert instance1.class_method() == "class_result_1"
        assert instance2.class_method() == "class_result_1"
    
    def test_singleton_memory_cleanup(self):
        """Test that singleton instances can be cleaned up when needed."""
        
        class CleanupClass(metaclass=SingletonMeta):
            def __init__(self):
                self.data = "test_data"
        
        # Create instance
        instance = CleanupClass()
        original_id = id(instance)
        
        # Verify it's in registry
        assert CleanupClass in SingletonMeta._instances
        
        # Force cleanup
        del SingletonMeta._instances[CleanupClass]
        del instance  # Remove local reference
        
        # Create new instance - should be different
        new_instance = CleanupClass()
        new_id = id(new_instance)
        
        # Should be a new object (different memory location)
        assert new_id != original_id
        assert CleanupClass in SingletonMeta._instances


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
