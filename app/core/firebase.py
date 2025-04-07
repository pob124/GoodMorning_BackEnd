from firebase_admin import auth, credentials, initialize_app, get_app
import os

# Firebase Admin SDK 초기화
def initialize_firebase():
    try:
        # 이미 초기화된 앱이 있는지 확인
        try:
            firebase_app = get_app()
            print("Firebase app already initialized")
            return None
        except ValueError:
            # 앱이 없는 경우 새로 초기화
            cred_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "docker/firebase-adminsdk.json")
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_app = initialize_app(cred)
                print("Firebase Admin SDK initialized successfully")
                return None  # 실제 Firebase Admin SDK는 직접 모듈로 접근
            else:
                print("Firebase credentials file not found, using mock Firebase")
                return MockFirebase()
    except Exception as e:
        print(f"Warning: Firebase initialization failed - {e}")
        print("Running in test mode with mock Firebase")
        return MockFirebase()

# 가짜 Firebase 클래스
class MockFirebase:
    def auth(self):
        return MockAuth()

class MockAuth:
    def sign_in_with_email_and_password(self, email, password):
        return {"idToken": "mock-token-12345"}
        
    def create_user(self, **kwargs):
        return MockUser("user123", kwargs.get("email", ""), kwargs.get("display_name", ""))

class MockUser:
    def __init__(self, uid, email, display_name):
        self.uid = uid
        self.email = email
        self.display_name = display_name

# 토큰 검증 함수
def verify_token(token):
    try:
        decoded_token = auth.verify_id_token(token)
        return decoded_token
    except Exception as e:
        print(f"Error verifying token: {e}")
        return None 