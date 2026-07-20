def sum_of_two_numbers():
    """Interactive calculator for summing two numbers"""
    print("=" * 40)
    print("   Interactive Sum Calculator")
    print("=" * 40)
    
    while True:
        try:
            # Get user input
            num1 = float(input("\nEnter first number1: "))
            num2 = float(input("Enter second number2: "))
            
            # Calculate sum
            result = num1 + num2
            
            # Display result
            print(f"\n{num1} + {num2} = {result}")
            
            # Ask if user wants to continue
            again = input("\nCalculate again? (yes/no): ").lower().strip()
            if again not in ['yes', 'y']:
                print("\nThank you for using Sum Calculator! Goodbye!\n")
                break
                
        except ValueError:
            print("❌ Invalid input! Please enter valid numbers.")

if __name__ == "__main__":
    sum_of_two_numbers()
