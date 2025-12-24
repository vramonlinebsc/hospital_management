from tasks import send_daily_appointment_reminders, send_monthly_doctor_reports

# Test 1
print("Testing daily reminders...")
result1 = send_daily_appointment_reminders.delay()
print(result1.get(timeout=60))

# Test 2
print("\nTesting monthly reports...")
result2 = send_monthly_doctor_reports.delay()
print(result2.get(timeout=60))
