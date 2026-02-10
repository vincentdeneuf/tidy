# This is a full-line comment that should be preserved
"""This is a docstring that should be preserved."""

def example_function():
    print("This should be removed")  # This inline comment should be removed
    x = 5  # type: int  # This comment should be preserved due to type:
    y = 10  # noqa: E501  # This comment should be preserved due to noqa
    z = 15  # pragma: no cover  # This comment should be preserved due to pragma
    
    print("Another print to remove")
    obj.print("This should not be removed")  # This comment should be removed
    
    return x + y + z

# Another full-line comment
print("Third print to remove")  # Final inline comment to remove
