from twilio.rest import Client
import os
import logging

class NotificationService:
    def __init__(self):
        # Twilio credentials (set these in environment variables)
        account_sid = os.getenv('TWILIO_ACCOUNT_SID')
        auth_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.from_number = os.getenv('TWILIO_PHONE_NUMBER')
        
        if account_sid and auth_token:
            self.client = Client(account_sid, auth_token)
            self.enabled = True
        else:
            logging.warning("Twilio credentials not found. SMS notifications disabled.")
            self.enabled = False
    
   def send_vehicle_arriving_sms(self, employee_mobile, vehicle_number, eta_minutes):
        """Send SMS when vehicle is arriving soon"""
        if not self.enabled:
            logging.info(f"[MOCK SMS] Vehicle {vehicle_number} arriving in {eta_minutes} mins to {employee_mobile}")
            return True
        
        try:
            message = f"🚗 Your transport vehicle {vehicle_number} is arriving in {eta_minutes} minutes. Please be ready!"
            
            self.client.messages.create(
                to=employee_mobile,
                from_=self.from_number,
                body=message
            )
            logging.info(f"SMS sent to {employee_mobile}: Vehicle arriving")
            return True
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_vehicle_arrived_sms(self, employee_mobile, vehicle_number, otp):
        """Send SMS when vehicle has arrived"""
        if not self.enabled:
            logging.info(f"[MOCK SMS] Vehicle {vehicle_number} arrived. OTP: {otp} to {employee_mobile}")
            return True
        
        try:
            message = f"✅ Your transport vehicle {vehicle_number} has arrived at your pickup location! Your OTP: {otp}"
            
            self.client.messages.create(
                to=employee_mobile,
                from_=self.from_number,
                body=message
            )
            logging.info(f"SMS sent to {employee_mobile}: Vehicle arrived")
            return True
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_trip_started_sms(self, employee_mobile, destination):
        """Send SMS when trip has started"""
        if not self.enabled:
            logging.info(f"[MOCK SMS] Trip started to {destination} for {employee_mobile}")
            return True
        
        try:
            message = f"🚀 Your trip to {destination} has started. Have a safe journey!"
            
            self.client.messages.create(
                to=employee_mobile,
                from_=self.from_number,
                body=message
            )
            logging.info(f"SMS sent to {employee_mobile}: Trip started")
            return True
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_trip_completed_sms(self, employee_mobile, destination):
        """Send SMS when trip is completed"""
        if not self.enabled:
            logging.info(f"[MOCK SMS] Trip completed to {destination} for {employee_mobile}")
            return True
        
        try:
            message = f"✓ You have reached {destination}. Thank you for using our transport service!"
            
            self.client.messages.create(
                to=employee_mobile,
                from_=self.from_number,
                body=message
            )
            logging.info(f"SMS sent to {employee_mobile}: Trip completed")
            return True
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False
    
    def send_schedule_notification_sms(self, employee_mobile, pickup_time, vehicle_number):
        """Send schedule reminder SMS"""
        if not self.enabled:
            logging.info(f"[MOCK SMS] Schedule reminder for {pickup_time} to {employee_mobile}")
            return True
        
        try:
            message = f"📅 Reminder: Your pickup is scheduled for {pickup_time} tomorrow. Vehicle: {vehicle_number}"
            
            self.client.messages.create(
                to=employee_mobile,
                from_=self.from_number,
                body=message
            )
            logging.info(f"SMS sent to {employee_mobile}: Schedule reminder")
            return True
        except Exception as e:
            logging.error(f"Error sending SMS: {str(e)}")
            return False


# Singleton instance
notification_service = NotificationService()
