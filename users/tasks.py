from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verification_email_task(email, verify_url):
    subject = 'Подтверждение почты в StockVision'
    message = f'Здравствуйте!\n\nПерейдите по ссылке, чтобы подтвердить вашу почту:\n{verify_url}\n\nЕсли вы не регистрировались на сайте, просто проигнорируйте это письмо.'
    from_email = 'StockVision <noreply@stockvision.com>'
    
    send_mail(
        subject,
        message,
        from_email,
        [email],
        fail_silently=False,
    )