from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from .models import DeliveryPersonApplication
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages

# Admin check decorator
# def admin_required(view_func):
#     return user_passes_test(lambda u: u.is_staff)(view_func)

# User application form

def get_user_application(request):
    if request.user.is_authenticated:
        try:
            return DeliveryPersonApplication.objects.get(email=request.user.email)
        except DeliveryPersonApplication.DoesNotExist:
            return None
    return None

def home(request):
    context = {
        'user_application': get_user_application(request)
    }
    return render(request, 'index.html', context)

def apply_for_job(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        resume = request.FILES.get('resume')

        if name and email and phone and resume:
            try:
                DeliveryPersonApplication.objects.create(
                    name=name,
                    email=email,
                    phone=phone,
                    resume=resume
                )
                messages.success(request, 'Your application has been submitted successfully! We will review it shortly.')
                return redirect('apply')
            except Exception as e:
                messages.error(request, 'An error occurred while submitting your application. Please try again.')
        else:
            messages.warning(request, 'Please fill in all the required fields.')
    else:
        # Check if user already has an application
        if request.user.is_authenticated:
            try:
                existing_app = DeliveryPersonApplication.objects.get(email=request.user.email)
                messages.info(request, 'You have already submitted an application. You can view and edit it below.')
            except DeliveryPersonApplication.DoesNotExist:
                pass

    context = {
        'user_application': get_user_application(request)
    }
    return render(request, 'apply.html', context)


# Admin-only view of applications with pagination + search
# @admin_required

@staff_member_required


def admin_applications_view(request):
    query = request.GET.get('search', '')
    applications = DeliveryPersonApplication.objects.all().order_by('-applied_on')

    if query:
        applications = applications.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )
        if not applications.exists():
            messages.info(request, 'No applications found matching your search criteria.')

    paginator = Paginator(applications, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'user_application': get_user_application(request)
    }
    return render(request, 'admin_applications.html', context)


def update_status(request, pk, status):
    app = get_object_or_404(DeliveryPersonApplication, pk=pk)
    if status in ['accepted', 'rejected']:
        app.status = status
        app.save()
        messages.success(request, f'Application status updated to {status.capitalize()}.')
    else:
        messages.error(request, 'Invalid status update.')
    return redirect('admin_applications')

def privacy(request):
    context = {
        'user_application': get_user_application(request)
    }
    return render(request, 'privacy_policy.html', context)

def apply(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        resume = request.FILES.get('resume')
        
        application = DeliveryPersonApplication(
            name=name,
            email=email,
            phone=phone,
            resume=resume
        )
        application.save()
        messages.success(request, 'Your application has been submitted successfully!')
        return redirect('apply')
    
    context = {
        'user_application': get_user_application(request)
    }
    return render(request, 'apply.html', context)

@login_required
def edit_application(request, application_id):
    application = get_object_or_404(DeliveryPersonApplication, id=application_id)
    
    if not request.user.is_superuser and application.email != request.user.email:
        messages.error(request, 'You do not have permission to edit this application.')
        return redirect('apply')
    
    if request.method == 'POST':
        try:
            application.name = request.POST.get('name')
            application.phone = request.POST.get('phone')
            if 'resume' in request.FILES:
                application.resume = request.FILES['resume']
            application.save()
            messages.success(request, 'Your application has been updated successfully!')
            return redirect('apply')
        except Exception as e:
            messages.error(request, 'An error occurred while updating your application. Please try again.')
    
    context = {
        'application': application,
        'user_application': get_user_application(request)
    }
    return render(request, 'edit_application.html', context)

@login_required
def delete_application(request, application_id):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to delete applications.')
        return redirect('apply')
    
    try:
        application = get_object_or_404(DeliveryPersonApplication, id=application_id)
        application.delete()
        messages.success(request, 'Application deleted successfully.')
    except Exception as e:
        messages.error(request, 'An error occurred while deleting the application.')
    return redirect('apply')