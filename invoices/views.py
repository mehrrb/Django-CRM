from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

from invoices.models import Invoice
from invoices.forms import InvoiceForm

@login_required
def invoices_list(request):
    invoices = Invoice.objects.filter(user=request.user)
    context = {'invoices': invoices}
    return render(request, 'invoices/invoices_list.html', context)

@login_required
def invoice_create(request):
    if request.method == 'POST':
        form = InvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.user = request.user
            invoice.save()
            return redirect('invoices:list')
    else:
        form = InvoiceForm()
    context = {'form': form}
    return render(request, 'invoices/invoice_create.html', context)

@login_required
def invoice_edit(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    if request.method == 'POST':
        form = InvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            return redirect('invoices:list')
    else:
        form = InvoiceForm(instance=invoice)
    context = {'form': form, 'invoice': invoice}
    return render(request, 'invoices/invoice_edit.html', context)

@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    invoice.delete()
    return redirect('invoices:list')

@login_required
def invoice_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    context = {'invoice': invoice}
    return render(request, 'invoices/invoice_view.html', context)

@login_required
def invoice_send_mail(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    subject = f'Invoice #{invoice.invoice_number}'
    message = render_to_string('invoices/invoice_email.html', {'invoice': invoice})
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [invoice.client_email]
    
    email = EmailMessage(subject, message, from_email, recipient_list)
    email.content_subtype = "html"
    email.send()
    
    return JsonResponse({'status': 'success'})

@login_required
def invoice_download_pdf(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, user=request.user)
    # Add PDF generation logic here
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{invoice.invoice_number}.pdf"'
    return response
