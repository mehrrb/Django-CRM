from datetime import datetime

import pytz
from celery import Celery, shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.template import Context, Template
from django.template.loader import render_to_string
from emails.models import Email

from users.models import Users
from accounts.models import Account, AccountEmailLog
from common.models import Profile
from common.utils import convert_to_custom_timezone

app = Celery("redis://")


@app.task
def send_email(email_obj_id):
    email_obj = Email.objects.filter(id=email_obj_id).first()
    if email_obj:
        from_email = email_obj.from_email
        contacts = email_obj.recipients.all()
        for contact_obj in contacts:
            if not AccountEmailLog.objects.filter(
                email=email_obj, contact=contact_obj, is_sent=True
            ).exists():
                html = email_obj.message_body
                context_data = {
                    "email": contact_obj.primary_email
                    if contact_obj.primary_email
                    else "",
                    "name": contact_obj.first_name
                    if contact_obj.first_name
                    else "" + " " + contact_obj.last_name
                    if contact_obj.last_name
                    else "",
                }
                try:
                    html_content = Template(html).render(Context(context_data))
                    subject = email_obj.message_subject
                    msg = EmailMessage(
                        subject,
                        html_content,
                        from_email=from_email,
                        to=[
                            contact_obj.primary_email,
                        ],
                    )
                    msg.content_subtype = "html"
                    res = msg.send()
                    if res:
                        email_obj.rendered_message_body = html_content
                        email_obj.save()
                        AccountEmailLog.objects.create(
                            email=email_obj, contact=contact_obj, is_sent=True
                        )
                except Exception as e:
                    print(e)


@app.task
def send_email_to_assigned_user(recipients, from_email):
    """Send Mail To Users When they are assigned to a contact"""
    account = Account.objects.filter(id=from_email).first()
    created_by = account.created_by

    for profile_id in recipients:
        recipients_list = []
        profile = Profile.objects.filter(id=profile_id, is_active=True).first()
        if profile:
            recipients_list.append(profile.user.email)
            context = {}
            context["url"] = settings.DOMAIN_NAME
            context["user"] = profile.user
            context["account"] = account
            context["created_by"] = created_by
            subject = "Assigned a account for you."
            html_content = render_to_string(
                "assigned_to/account_assigned.html", context=context
            )

            msg = EmailMessage(subject, html_content, to=recipients_list)
            msg.content_subtype = "html"
            msg.send()

@shared_task
def send_account_assigned_emails(account_id, recipients):
    """Send email notifications when an account is assigned to users"""
    
    if not recipients:
        return
        
    account = Account.objects.filter(id=account_id).first()
    if not account:
        return
        
    subject = _("Account Assigned: {}").format(account.name)
    
    context = {
        'account_name': account.name,
        'account_link': settings.DOMAIN_NAME + f'/accounts/{account.id}/view/',
        'assigned_by': account.created_by.email if account.created_by else '',
    }
    
    html_content = render_to_string('email_templates/account_assigned.html', context)
    
    for user_id in recipients:
        user = Users.objects.filter(id=user_id).first()
        if not user:
            continue
            
        msg = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )
        msg.content_subtype = "html"
        msg.send()

    return True

@app.task
def send_scheduled_emails():
    email_objs = Email.objects.filter(scheduled_later=True)
    # TODO: modify this later , since models are updated
    for each in email_objs:
        scheduled_date_time = each.scheduled_date_time

        sent_time = datetime.now().strftime("%Y-%m-%d %H:%M")
        sent_time = datetime.strptime(sent_time, "%Y-%m-%d %H:%M")
        local_tz = pytz.timezone(settings.TIME_ZONE)
        sent_time = local_tz.localize(sent_time)
        sent_time = convert_to_custom_timezone(sent_time, each.timezone, to_utc=True)

        # if (
        #     str(each.scheduled_date_time.date()) == str(sent_time.date()) and
        #     str(scheduled_date_time.hour) == str(sent_time.hour) and
        #     (str(scheduled_date_time.minute + 5) < str(sent_time.minute) or
        #     str(scheduled_date_time.minute - 5) > str(sent_time.minute))
        # ):
        #     send_email.delay(each.id)
        if (
            str(each.scheduled_date_time.date()) == str(sent_time.date())
            and str(scheduled_date_time.hour) == str(sent_time.hour)
            and str(scheduled_date_time.minute) == str(sent_time.minute)
        ):
            send_email.delay(each.id)

@shared_task
def send_account_status_email(account_id, status_changed_by_id=None):
    """Send email when account status changes"""
    try:
        account = Account.objects.filter(id=account_id).first()
        if not account:
            return False

        changed_by = None
        if status_changed_by_id:
            changed_by = Profile.objects.filter(id=status_changed_by_id).first()

        context = {
            'account': account,
            'changed_by': changed_by.user.email if changed_by else 'System',
            'url': settings.DOMAIN_NAME,
        }

        subject = f"Account Status Updated: {account.name}"
        html_content = render_to_string(
            'email_templates/account_status_update.html',
            context=context
        )

        recipients = []
        if account.email:
            recipients.append(account.email)

        if recipients:
            msg = EmailMessage(
                subject=subject,
                body=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipients
            )
            msg.content_subtype = "html"
            return msg.send()
        return False
        
    except Exception as e:
        print(f"Error sending account status email: {str(e)}")
        return False

@shared_task
def send_account_deleted_email(account_email, deleted_by_email=None):
    """Send email when account is deleted"""
    try:
        subject = "Account Deleted"
        context = {
            'deleted_by': deleted_by_email if deleted_by_email else 'System',
            'url': settings.DOMAIN_NAME,
        }
        
        html_content = render_to_string(
            'email_templates/account_deleted.html',
            context=context
        )
        
        msg = EmailMessage(
            subject=subject,
            body=html_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[account_email]
        )
        msg.content_subtype = "html"
        return msg.send()
    except Exception as e:
        print(f"Error sending account deleted email: {str(e)}")
        return False
