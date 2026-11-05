from django.core.mail import send_mail

class NotificationService:

    @staticmethod
    def notify(subject, message, recipient):
        send_mail(
            subject,
            message,
            None,
            [recipient],
            fail_silently=True
        )
