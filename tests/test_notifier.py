from unittest.mock import patch, MagicMock
from src.notifier import send_email

def test_send_email_ssl_success():
    config = {
        "SMTP_HOST": "smtp.gmail.com",
        "SMTP_PORT": 465,
        "SMTP_USER": "test@gmail.com",
        "SMTP_PASS": "mock-pass",
        "RECEIVER_EMAIL": "receiver@gmail.com"
    }
    with patch("smtplib.SMTP_SSL") as mock_smtp:
        instance = MagicMock()
        mock_smtp.return_value.__enter__.return_value = instance
        
        ok = send_email("今日早报", "<p>Hello</p>", config=config)
        assert ok is True
        instance.login.assert_called_once_with("test@gmail.com", "mock-pass")
        instance.send_message.assert_called_once()

def test_send_email_missing_config():
    ok = send_email("今日早报", "<p>Hello</p>", config={})
    assert ok is False
