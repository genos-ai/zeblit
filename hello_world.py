print("Hello, World!")
print("This is a test Python script in Zeblit!")

def greet(name):
    return f"Hello, {name}! Welcome to Zeblit AI Platform."

if __name__ == "__main__":
    print(greet("Developer"))
    
    # Test some basic functionality
    numbers = [1, 2, 3, 4, 5]
    print(f"Sum of numbers {numbers}: {sum(numbers)}")
    
    # Test file operations
    with open("test_output.txt", "w") as f:
        f.write("This file was created by our test script!\\n")
    
    print("Created test_output.txt file")
    print("Test complete!")
