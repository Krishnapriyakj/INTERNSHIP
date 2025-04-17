# services/payment_service.py
import qrcode
import time
import uuid
import matplotlib.pyplot as plt

UPI_ID = "bexcybiju0209@oksbi"
token_tracker = {}

def calculate_fee(age: int) -> float:
    return 20.00 if 18 <= age <= 50 else 0.00

def generate_qr_code(name: str, fee: float) -> str:
    transaction_id = str(uuid.uuid4())[:12]
    upi_url = f"upi://pay?pa={UPI_ID}&pn={name}&am={fee}&cu=INR&tr={transaction_id}&tn=HospitalAppointmentFee"
    qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=10, border=4)
    qr.add_data(upi_url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    plt.figure(figsize=(6, 6))
    plt.imshow(qr_img, cmap="gray")
    plt.axis("off")
    plt.title("Scan the QR Code to Pay")
    plt.show()
    return transaction_id

def simulate_payment_verification(transaction_id: str, timeout: int = 60) -> bool:
    print(f"Simulating payment verification for transaction {transaction_id}...")
    start_time = time.time()
    while time.time() - start_time < timeout:
        confirmation = input("Enter 'yes' to simulate successful payment, 'no' to fail: ").strip().lower()
        if confirmation == "yes":
            return True
        elif confirmation == "no":
            return False
        time.sleep(5)
    return False

def generate_token(department: str, time_slot: str) -> tuple[int, str]:
    key = (department, time_slot)
    token_tracker[key] = token_tracker.get(key, 0) + 1
    return token_tracker[key], f"{time_slot}:00 - {time_slot}:15"

def process_payment(age: int, name: str, department: str, time_slot: str, hospital_info: dict) -> str:
    fee = calculate_fee(age)
    
    if fee == 0:
        token, time_block = generate_token(department, time_slot)
        return f"Appointment confirmed (no fee required).\nHospital: {hospital_info['Hospital Name']}\nDoctor: {hospital_info['Doctor']}\nDepartment: {department}\nTime: {time_block}\nToken: {token}"
    
    print(f"Fee of ₹{fee} required. Please scan the QR code.")
    transaction_id = generate_qr_code(name, fee)
    
    if simulate_payment_verification(transaction_id):
        token, time_block = generate_token(department, time_slot)
        return f"Payment successful!\nAppointment confirmed:\nHospital: {hospital_info['Hospital Name']}\nDoctor: {hospital_info['Doctor']}\nDepartment: {department}\nTime: {time_block}\nToken: {token}"
    else:
        return "Payment failed or timed out. Please try booking again."