import qrcode
import time
import uuid
import matplotlib.pyplot as plt
from datetime import datetime

# Token tracker for generating tokens
token_tracker = {}

def calculate_fee(age: int) -> float:
    """
    Calculate the fee based on the user's age.
    - If age is between 18 and 50, the fee is ₹20.
    - Otherwise, the fee is ₹0.
    """
    return 20.00 if 18 <= age <= 50 else 0.00

def generate_qr_code(upi_id: str, name: str, fee: float) -> str:
    """
    Generate and display a QR code for UPI payment.
    Returns a unique transaction ID for tracking.
    """
    unique_transaction_id = str(uuid.uuid4())[:12]  # Generate a unique 12-character ID
    upi_payment_url = (
        f"upi://pay?pa={upi_id}&pn={name}&am={fee}&cu=INR&tr={unique_transaction_id}&tn=HospitalAppointmentFee"
    )
    print(f"Generated UPI Payment URL: {upi_payment_url}")

    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_payment_url)
    qr.make(fit=True)

    qr_code_image = qr.make_image(fill_color="black", back_color="white")

    # Display the QR code
    plt.figure(figsize=(6, 6))
    plt.imshow(qr_code_image, cmap="gray")
    plt.axis("off")
    plt.title("Scan the QR Code to Pay")
    plt.show()

    return unique_transaction_id  # Return transaction ID for tracking

def simulate_payment_confirmation(transaction_id: str) -> bool:
    """
    Simulate payment confirmation by asking the user to confirm the payment.
    """
    print(f"Simulating payment confirmation for transaction ID: {transaction_id}")
    confirmation = input("Did you complete the payment? (yes/no): ").strip().lower()
    return confirmation == "yes"

def wait_for_payment(transaction_id: str, timeout: int = 600) -> bool:
    """
    Wait for a payment to complete within the timeout period.
    Returns True if payment is successful, otherwise False.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        if simulate_payment_confirmation(transaction_id):
            print(f"Payment verified for transaction ID {transaction_id}.")
            return True
        time.sleep(10)  # Poll every 10 seconds
    print(f"Payment not received for transaction ID {transaction_id} within timeout.")
    return False

def generate_token(department: str, time_slot: str) -> tuple[int, str]:
    """
    Generate a token for the appointment.
    - `department`: The department for which the token is being generated.
    - `time_slot`: The time slot for the appointment (e.g., "10:00").
    Returns a tuple containing the token number and the time block.
    """
    hour, minute = map(int, time_slot.split(':'))
    minute_block = (minute // 15) * 15
    block_start_time = f"{hour:02}:{minute_block:02}"

    # Increment the token for the department and time block
    key = (department, block_start_time)
    token_tracker[key] = token_tracker.get(key, 0) + 1

    # Return the token number and the 15-minute block
    return token_tracker[key], f"{block_start_time}:00 to {hour:02}:{minute_block + 15:02}:00"

def process_payment_and_generate_token(age: int, upi_id: str, name: str, department: str, time_slot: str) -> tuple[bool, int, str]:
    """
    Process payment and generate a token for the appointment.
    - `age`: The user's age.
    - `upi_id`: The UPI ID for payment.
    - `name`: The user's name.
    - `department`: The department for the appointment.
    - `time_slot`: The time slot for the appointment.
    Returns a tuple containing:
    - A boolean indicating whether the payment was successful.
    - The token number (if payment was successful).
    - The time block for the appointment (if payment was successful).
    """
    fee = calculate_fee(age)
    if fee == 0:
        print("No payment required. Proceeding with appointment confirmation.")
        token, time_block = generate_token(department, time_slot)
        return True, token, time_block

    print(f"An appointment fee of ₹{fee} is required.")
    try:
        unique_transaction_id = generate_qr_code(upi_id, name, fee)
        print("Please complete the payment by scanning the QR code.")

        if wait_for_payment(unique_transaction_id):
            print("Payment successful. Proceeding with appointment confirmation.")
            token, time_block = generate_token(department, time_slot)
            return True, token, time_block
        else:
            print("Payment verification failed or timed out.")
            return False, None, None
    except Exception as e:
        print(f"Payment processing failed. Error: {e}")
        return False, None, None