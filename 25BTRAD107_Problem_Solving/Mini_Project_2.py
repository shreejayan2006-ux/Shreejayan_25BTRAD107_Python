# Generate a random six-digit OTP
otp = random.randint(100000,
999999)
print("================================")
print(" OTP GENERATOR")
print("================================")
print("Your OTP is:", otp)
# Take OTP input from the user entered_otp
= int(input("Enter the OTP: "))
# Verify the OTP if
entered_otp == otp:
print("OTP verified successfully!") else:
print("Invalid OTP. Verification failed.")
print("================================")
