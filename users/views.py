
from django.core.mail import EmailMultiAlternatives
from users.admin import MyUserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
from users.forms import LoginForm, UploadFileForm, UploadProfileImage #ContactForm, ChangePasswordForm
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from helpers.upload import handle_upload_file
from django.template.loader import get_template
from users.forms import ContactForm
# from django.contrib.sites.models import Site #v1 din register
# used for reset password
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash


def handle_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                return HttpResponseRedirect(reverse('users:profile'))
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {
        'form': form
    })


def handle_logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('users:login'))


@login_required
def profile(request):
    if request.method == 'POST':
        user_profile = request.user.profile
        form = UploadProfileImage(request.POST, request.FILES, instance=user_profile)

        if form.is_valid():
            user_profile = form.save(commit=False)
            user_profile.user = request.user
            user_profile.save()
            return HttpResponseRedirect(reverse('users:profile'))

    else:
        form = UploadProfileImage()

    return render(request, 'users/profile.html', {'form': form})


@login_required
def profile_email(request):

    email_template = get_template('users/email.html')
    email_content = email_template.render(
        {
            'your_profile': request.user.profile,
            'your_email': request.user.email,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
        })

    mail = EmailMultiAlternatives(
        'Your profile data request',
        email_content,
        settings.EMAIL_HOST_USER,
        [request.user.email])

    mail.content_subtype = 'html'
    mail.attach_file('{BASE_DIR}/{MEDIA_ROOT}/{PROFILE_IMAGE}'.format(
        BASE_DIR=settings.BASE_DIR,
        MEDIA_ROOT=settings.MEDIA_ROOT,
        PROFILE_IMAGE=request.user.profile.avatar))
    mail.send()

    return HttpResponseRedirect(reverse('users:profile'))


def register(request):
    # current_site = Site.objects.get_current()

    if request.method == 'POST':
        form = MyUserCreationForm(request.POST)

        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('users:login'))
    else:
        form = MyUserCreationForm()

    return render(request, 'users/register.html', {
                        # 'host': current_site.domain,
                        'form': form
                   })


# inca nu am folosit acest view
def upload(request):

    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)

        if form.is_valid():
            my_file = form.cleaned_data['my_file']
            handle_upload_file(my_file)
    else:
        form = UploadFileForm()
    return render(request, 'users/upload.html', {'form': form})


# def contact_view(request):
#     # form = ContactForm(request.POST)
#     # if form.is_valid():
#     #     return render(request, 'users/contact.html', {'form': form})
#
#     return render(request, "users/contact.html")


def contact_view(request):

    form = ContactForm(request.POST)

    # if request.user.is_authenticated:
    #     print(request.user.last_name * 8)
    #     remail = request.user.email
    #     rfirst_name = request.user.first_name
    #     rlast_name = request.user.last_name
    #     form.email = remail
    #     form.last_name = rlast_name
    #     form.first_name = rfirst_name
    #     print(form.first_name * 8)

    if form.is_valid():
        # if request.user.is_authenticated:
        #     first_name = form.cleaned_data[request.user.first_name]
        #     print(first_name * 8)
        #     last_name = form.cleaned_data[request.user.last_name]
        #     email = form.cleaned_data[request.user.email]
        # else:
        first_name = form.cleaned_data['first_name']

        last_name = form.cleaned_data['last_name']
        email = form.cleaned_data['email']
        mobile = form.cleaned_data['mobile']
        subject = form.cleaned_data['subject']
        message = form.cleaned_data['message']
        email_template = get_template('users/contact_email_send.html')

        email_content = email_template.render(
            {

                'first_name': first_name,
                'last_name': last_name,
                'email': email,
                'mobile': mobile,
                'subject': subject,
                'message': message,
            }
        )

        mail = EmailMultiAlternatives(
            f'Visit Romania:{subject}',
            email_content,
            settings.EMAIL_HOST_USER,
            [email],
            (settings.EMAIL_HOST_USER, )
        )
        mail.content_subtype = 'html'
        mail.send()

        return HttpResponseRedirect(reverse('users:contact'))

    return render(request, "users/contact.html", {'form': form})


# @login_required
# def change_password(request):
#     form = ChangePasswordForm(request.POST)
#     if request.method == 'POST':
#         if form.is_valid():
#             new_password = form.cleaned_data['new_password']
#             confirm_password = form.cleaned_data['confirm_password']
#             # password = form.cleaned_data['password']
#             if new_password == confirm_password:
#                 # password = confirm_password
#                 return HttpResponseRedirect(reverse('users:profile'))
#
#     return render(request, "users/change_password.html", {'form': form})

#
# <form method="post" action="{% url 'users:change_password'  %}">
#                 {% csrf_token %}
#                 {{ form.as_p }}
#     <input type="submit" class="btn btn-primary mb-2" value="Change password" />
# </form>


@login_required()
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password was successfully updated!')
            return redirect('users:profile')
        else:
            messages.error(request, 'Please correct the error below.')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'users/change_password.html', {
        'form': form
    })
    pass




