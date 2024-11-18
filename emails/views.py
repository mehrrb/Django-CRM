from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings

from emails.models import Email
from emails.forms import EmailForm

@login_required
def emails_list(request):
    emails = Email.objects.filter(user=request.user)
    context = {'emails': emails}
    return render(request, 'emails/emails_list.html', context)

@login_required
def email_compose(request):
    form = EmailForm()
    context = {'form': form}
    return render(request, 'emails/email_compose.html', context)

@login_required
def email_send(request):
    if request.method == 'POST':
        form = EmailForm(request.POST)
        if form.is_valid():
            email = form.save(commit=False)
            email.user = request.user
            email.save()
            
            # Send actual email
            subject = email.subject
            message = email.message
            from_email = settings.DEFAULT_FROM_EMAIL
            recipient_list = [email.to_email]
            
            email_message = EmailMessage(subject, message, from_email, recipient_list)
            email_message.send()
            
            return redirect('emails:email_sent')
    return redirect('emails:compose')

@login_required
def email_sent(request):
    emails = Email.objects.filter(user=request.user, is_sent=True)
    context = {'emails': emails}
    return render(request, 'emails/email_sent.html', context)

@login_required
def email_move_to_trash(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email = get_object_or_404(Email, id=email_id, user=request.user)
        email.is_trash = True
        email.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def email_delete(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email = get_object_or_404(Email, id=email_id, user=request.user)
        email.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def email_trash(request):
    emails = Email.objects.filter(user=request.user, is_trash=True)
    context = {'emails': emails}
    return render(request, 'emails/email_trash.html', context)

@login_required
def email_draft(request):
    emails = Email.objects.filter(user=request.user, is_draft=True)
    context = {'emails': emails}
    return render(request, 'emails/email_draft.html', context)

@login_required
def email_draft_delete(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email = get_object_or_404(Email, id=email_id, user=request.user, is_draft=True)
        email.delete()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def email_imp_list(request):
    emails = Email.objects.filter(user=request.user, is_important=True)
    context = {'emails': emails}
    return render(request, 'emails/email_important.html', context)

@login_required
def email_mark_as_important(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email = get_object_or_404(Email, id=email_id, user=request.user)
        email.is_important = True
        email.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def email_mark_as_not_important(request):
    if request.method == 'POST':
        email_id = request.POST.get('email_id')
        email = get_object_or_404(Email, id=email_id, user=request.user)
        email.is_important = False
        email.save()
        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'error'})

@login_required
def email_sent_edit(request, pk):
    email = get_object_or_404(Email, id=pk, user=request.user)
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=email)
        if form.is_valid():
            form.save()
            return redirect('emails:email_sent')
    else:
        form = EmailForm(instance=email)
    context = {'form': form, 'email': email}
    return render(request, 'emails/email_sent_edit.html', context)

@login_required
def email_sent_delete(request, pk):
    email = get_object_or_404(Email, id=pk, user=request.user)
    email.delete()
    return redirect('emails:email_sent')

@login_required
def email_trash_delete(request, pk):
    email = get_object_or_404(Email, id=pk, user=request.user, is_trash=True)
    email.delete()
    return redirect('emails:email_trash')
