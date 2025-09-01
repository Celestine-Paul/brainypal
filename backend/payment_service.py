import requests
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os
from models import Subscription, db
import logging

class PaystackPaymentProcessor:
    def __init__(self):
        # Paystack API configuration
        self.secret_key = os.environ.get('PAYSTACK_SECRET_KEY', 'sk_test_your_paystack_secret_key')
        self.public_key = os.environ.get('PAYSTACK_PUBLIC_KEY', 'pk_test_your_paystack_public_key')
        
        # Paystack API base URL
        self.base_url = "https://api.paystack.co"
        
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json"
        }
        
        # Kenyan pricing in KES (Paystack supports KES)
        self.plans = {
            'premium': {
                'name': 'Premium Plan',
                'amount': 99900,  # KES 999 in kobo (multiply by 100)
                'currency': 'KES',
                'interval': 'monthly',
                'features': [
                    '100 flashcards per day',
                    '25 quizzes per day',
                    '5 AI study plans per month',
                    'Advanced analytics',
                    'Priority support'
                ]
            },
            'pro': {
                'name': 'Pro Plan', 
                'amount': 199900,  # KES 1999 in kobo
                'currency': 'KES',
                'interval': 'monthly',
                'features': [
                    'Unlimited flashcards',
                    'Unlimited quizzes',
                    'Unlimited AI study plans',
                    'Advanced analytics',
                    'Team collaboration',
                    'API access'
                ]
            }
        }
    
    def initialize_payment(self, user_id: int, plan_type: str, user_email: str) -> Dict:
        """Initialize Paystack payment transaction"""
        try:
            plan = self.plans.get(plan_type)
            if not plan:
                return {'success': False, 'error': 'Invalid plan type'}
            
            # Generate unique reference
            reference = f"brainypal_{user_id}_{plan_type}_{int(datetime.now().timestamp())}"
            
            payload = {
                "email": user_email,
                "amount": plan['amount'],  # Amount in kobo
                "currency": plan['currency'],
                "reference": reference,
                "callback_url": f"{os.environ.get('FRONTEND_URL', 'http://localhost:8080')}/payment/success",
                "metadata": {
                    "user_id": user_id,
                    "plan_type": plan_type,
                    "subscription": True
                }
            }
            
            response = requests.post(
                f"{self.base_url}/transaction/initialize",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status']:
                    # Store pending subscription
                    self._create_pending_subscription(user_id, plan_type, reference)
                    
                    return {
                        'success': True,
                        'authorization_url': result['data']['authorization_url'],
                        'access_code': result['data']['access_code'],
                        'reference': result['data']['reference']
                    }
                else:
                    return {'success': False, 'error': result.get('message', 'Payment initialization failed')}
            else:
                return {'success': False, 'error': f"Paystack API error: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Paystack payment initialization failed: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def verify_payment(self, reference: str) -> Dict:
        """Verify payment with Paystack"""
        try:
            response = requests.get(
                f"{self.base_url}/transaction/verify/{reference}",
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if result['status']:
                    data = result['data']
                    return {
                        'success': True,
                        'status': data['status'],
                        'amount': data['amount'],
                        'currency': data['currency'],
                        'reference': data['reference'],
                        'customer_email': data['customer']['email'],
                        'metadata': data.get('metadata', {}),
                        'transaction_data': data
                    }
                else:
                    return {'success': False, 'error': result.get('message', 'Payment verification failed')}
            else:
                return {'success': False, 'error': f"Verification failed: {response.status_code}"}
                
        except Exception as e:
            logging.error(f"Payment verification error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def handle_webhook(self, webhook_data: Dict, signature: str = None) -> Dict:
        """Handle Paystack webhook notifications"""
        try:
            event = webhook_data.get('event')
            data = webhook_data.get('data', {})
            
            logging.info(f"Webhook received: {event}")
            
            if event == 'charge.success':
                return self._handle_successful_payment(data)
            elif event == 'charge.failed':
                return self._handle_failed_payment(data)
            elif event == 'subscription.create':
                return self._handle_subscription_created(data)
            elif event == 'subscription.disable':
                return self._handle_subscription_cancelled(data)
            
            return {'success': True, 'message': 'Webhook processed'}
            
        except Exception as e:
            logging.error(f"Webhook handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _create_pending_subscription(self, user_id: int, plan_type: str, reference: str):
        """Create pending subscription record"""
        try:
            subscription = Subscription.query.filter_by(user_id=user_id).first()
            
            if subscription:
                subscription.plan_type = plan_type
                subscription.status = 'pending'
                subscription.payment_id = reference
            else:
                subscription = Subscription(
                    user_id=user_id,
                    plan_type=plan_type,
                    status='pending',
                    payment_id=reference
                )
                db.session.add(subscription)
            
            db.session.commit()
            
        except Exception as e:
            logging.error(f"Error creating pending subscription: {str(e)}")
    
    def _handle_successful_payment(self, payment_data: Dict) -> Dict:
        """Handle successful payment from webhook"""
        try:
            reference = payment_data.get('reference')
            metadata = payment_data.get('metadata', {})
            user_id = metadata.get('user_id')
            plan_type = metadata.get('plan_type')
            
            if not user_id or not plan_type:
                # Try to extract from reference
                if reference and 'brainypal_' in reference:
                    parts = reference.split('_')
                    if len(parts) >= 3:
                        user_id = int(parts[1])
                        plan_type = parts[2]
            
            if user_id and plan_type:
                subscription = Subscription.query.filter_by(user_id=user_id).first()
                
                if subscription:
                    subscription.plan_type = plan_type
                    subscription.status = 'active'
                    subscription.payment_id = reference
                    subscription.start_date = datetime.utcnow()
                    subscription.end_date = datetime.utcnow() + timedelta(days=30)
                else:
                    subscription = Subscription(
                        user_id=user_id,
                        plan_type=plan_type,
                        status='active',
                        payment_id=reference,
                        start_date=datetime.utcnow(),
                        end_date=datetime.utcnow() + timedelta(days=30)
                    )
                    db.session.add(subscription)
                
                db.session.commit()
                
                logging.info(f"Subscription activated for user {user_id}, plan {plan_type}")
                return {'success': True, 'message': 'Subscription activated'}
            
            return {'success': False, 'error': 'Unable to extract user info from payment'}
            
        except Exception as e:
            logging.error(f"Error handling successful payment: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_failed_payment(self, payment_data: Dict) -> Dict:
        """Handle failed payment"""
        try:
            reference = payment_data.get('reference')
            logging.warning(f"Payment failed for reference {reference}")
            
            # Update subscription status if exists
            subscription = Subscription.query.filter_by(payment_id=reference).first()
            if subscription:
                subscription.status = 'failed'
                db.session.commit()
            
            return {'success': True, 'message': 'Payment failure handled'}
            
        except Exception as e:
            logging.error(f"Error handling payment failure: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_created(self, subscription_data: Dict) -> Dict:
        """Handle subscription creation"""
        try:
            logging.info("Subscription created via Paystack")
            return {'success': True, 'message': 'Subscription creation handled'}
            
        except Exception as e:
            logging.error(f"Error handling subscription creation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_subscription_cancelled(self, subscription_data: Dict) -> Dict:
        """Handle subscription cancellation"""
        try:
            subscription_code = subscription_data.get('subscription_code')
            
            # Find and update subscription
            subscription = Subscription.query.filter_by(payment_id=subscription_code).first()
            if subscription:
                subscription.status = 'cancelled'
                subscription.end_date = datetime.utcnow()
                db.session.commit()
            
            logging.info(f"Subscription cancelled: {subscription_code}")
            return {'success': True, 'message': 'Subscription cancelled'}
            
        except Exception as e:
            logging.error(f"Error handling subscription cancellation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def get_payment_methods(self) -> List[Dict]:
        """Get available payment methods in Kenya via Paystack"""
        return [
            {
                'id': 'card',
                'name': 'Debit/Credit Card',
                'description': 'Visa, Mastercard, Verve',
                'icon': '💳',
                'supported': True,
                'popular': True
            },
            {
                'id': 'bank_transfer',
                'name': 'Bank Transfer',
                'description': 'Direct bank payment',
                'icon': '🏦',
                'supported': True,
                'popular': False
            },
            {
                'id': 'ussd',
                'name': 'USSD',
                'description': 'Pay with USSD code',
                'icon': '📱',
                'supported': True,
                'popular': True
            },
            {
                'id': 'qr',
                'name': 'QR Code',
                'description': 'Scan to pay',
                'icon': '📷',
                'supported': True,
                'popular': False
            }
        ]
    
    def cancel_subscription(self, user_id: int) -> Dict:
        """Cancel user subscription"""
        try:
            subscription = Subscription.query.filter_by(user_id=user_id).first()
            
            if not subscription or subscription.plan_type == 'free':
                return {'success': False, 'error': 'No active subscription to cancel'}
            
            # If it's a Paystack subscription, disable it
            if subscription.payment_id and subscription.payment_id.startswith('sub_'):
                payload = {"code": subscription.payment_id, "token": subscription.payment_id}
                response = requests.post(
                    f"{self.base_url}/subscription/disable",
                    headers=self.headers,
                    json=payload
                )
            
            # Update local subscription
            subscription.status = 'cancelled'
            subscription.end_date = datetime.utcnow()
            db.session.commit()
            
            return {'success': True, 'message': 'Subscription cancelled successfully'}
            
        except Exception as e:
            logging.error(f"Subscription cancellation error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """Validate Paystack webhook signature"""
        try:
            webhook_secret = os.environ.get('PAYSTACK_WEBHOOK_SECRET', '')
            if not webhook_secret:
                return True  # Skip validation if no secret set
            
            hash_object = hmac.new(
                webhook_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha512
            )
            
            expected_signature = hash_object.hexdigest()
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logging.error(f"Webhook signature validation error: {str(e)}")
            return False
    
    def get_transaction_history(self, user_id: int) -> Dict:
        """Get user's transaction history"""
        try:
            subscriptions = Subscription.query.filter_by(user_id=user_id).all()
            
            transactions = []
            for sub in subscriptions:
                if sub.payment_id and sub.payment_id != 'demo':
                    transactions.append({
                        'id': sub.id,
                        'plan_type': sub.plan_type,
                        'amount': self.plans.get(sub.plan_type, {}).get('amount', 0) / 100,  # Convert from kobo
                        'currency': 'KES',
                        'status': sub.status,
                        'date': sub.created_at.isoformat(),
                        'reference': sub.payment_id
                    })
            
            return {
                'success': True,
                'transactions': transactions
            }
            
        except Exception as e:
            logging.error(f"Error getting transaction history: {str(e)}")
            return {'success': False, 'error': str(e)}

# Flask routes for Paystack integration
def setup_paystack_routes(app):
    """Setup Paystack payment routes"""
    
    @app.route('/api/payment/initialize', methods=['POST'])
    def initialize_paystack_payment():
        from flask import request, jsonify
        
        try:
            data = request.get_json()
            processor = PaystackPaymentProcessor()
            
            result = processor.initialize_payment(
                user_id=data['user_id'],
                plan_type=data['plan_type'],
                user_email=data['email']
            )
            
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/payment/webhook', methods=['POST'])
    def handle_paystack_webhook():
        from flask import request
        
        try:
            webhook_data = request.get_json()
            signature = request.headers.get('X-Paystack-Signature')
            
            processor = PaystackPaymentProcessor()
            
            # Validate signature
            if signature:
                payload = request.get_data(as_text=True)
                if not processor.validate_webhook_signature(payload, signature):
                    return 'Invalid signature', 400
            
            result = processor.handle_webhook(webhook_data)
            
            if result['success']:
                return '', 200
            else:
                return result['error'], 400
                
        except Exception as e:
            logging.error(f"Webhook processing error: {str(e)}")
            return 'Webhook processing failed', 500
    
    @app.route('/api/payment/verify/<reference>', methods=['GET'])
    def verify_paystack_payment(reference):
        from flask import jsonify
        
        try:
            processor = PaystackPaymentProcessor()
            result = processor.verify_payment(reference)
            return jsonify(result)
            
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

# Create alias for backward compatibility
PaymentProcessor = PaystackPaymentProcessor