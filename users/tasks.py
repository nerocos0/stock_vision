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

@shared_task
def send_password_reset_email_task(email, reset_password_url):
    subject = 'Восстановление пароля в StockVision'
    message = f'Здравствуйте!\n\nПерейдите по ссылке, чтобы восстановить пароль:\n{reset_password_url}\n\nЕсли вы не регистрировались на сайте, просто проигнорируйте это письмо.'
    from_email = 'StockVision <noreply@stockvision.com>'

    send_mail(
        subject,
        message,
        from_email,
        [email],
        fail_silently=False,
    )  

@shared_task
def send_email_change_task(old_email, new_email, verify_url):
    subject = 'Подтверждение смены email в StockVision'
    message = (
        f'Вы запросили смену email с {old_email} на {new_email}.\n\n'
        f'Перейдите по ссылке, чтобы подтвердить смену:\n{verify_url}\n\n'
        f'Если вы не запрашивали смену, просто проигнорируйте это письмо.'
    )
    from_email = 'StockVision <noreply@stockvision.com>'
    send_mail(
        subject,
        message,
        from_email,
        [new_email],
        fail_silently=False
    )  