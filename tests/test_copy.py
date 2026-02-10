#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This is a header comment that should be removed with --header

"""This is a module docstring that should be removed with tidy docstrings."""

# This is a leading comment that should be removed with --leading
def example_function():
    """This is a function docstring that should be removed with tidy docstrings."""
    x = 5  # type: int  # This comment should be preserved by default, removed with --inline
    y = 10  # noqa: E501  # This comment should be preserved by default, removed with --inline
    z = 15  # pragma: no cover  # This comment should be preserved by default, removed with --inline
    
    assert x > 0, "x must be positive"  # This assert should be removed with tidy asserts
    assert y is not None  # This assert should be removed with tidy asserts
    log.debug("This is a debug log")
    log.info("This is an info log")
    log.warning("This is a warning log")
    log.success("This is a success log")
    log.exception("This is an exception log")
    log.critical("This is a critical log")
    
    # More logging with different base names
    logger.debug("Logger debug message")
    logger.info("Logger info message")
    logging.warning("Logging warning message")
    
    # These should NOT be removed (not standalone expressions)
    x = logger.info("This should not be removed")
    logger.debug("This should not be removed").strip()
    custom_logger.info("This should not be removed")
    obj.print("This should not be removed")  # This comment should be removed
    
    return x + y + z

class ExampleClass:
    """This is a class docstring that should be removed with tidy docstrings."""
    
    def method(self):
        """This is a method docstring that should be removed with tidy docstrings."""
        assert True  # This assert should be removed with tidy asserts
        
        # Logging in method
        log.info("Method log message")
        logger.debug("Method logger debug")
        
        return 42
