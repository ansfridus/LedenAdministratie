from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import send_mail
from django.template.loader import render_to_string
import django.http

from .models import Lid
from . import forms
from . import settings


def login(request):
    form = forms.LoginForm()

    if request.method == 'POST':
        form = forms.LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            url = reverse_lazy('openid_login')
            url += '?openid=%s/%s' % ('https://login.scouting.nl/user', username)
            return django.http.HttpResponseRedirect(url)

    return render(request, 'login.html', {'form': form})


def check_user(user):
    if user.is_authenticated and user.has_perm('LedenAdministratie.read_lid') and user.is_active:
        return True
    return False


@user_passes_test(check_user)
def logoff(request):
    logout(request)

    full_url = request.build_absolute_uri('/')

    return django.http.HttpResponseRedirect('https://login.scouting.nl/provider/logout/?submit=logout&openid_return_url=%s' % full_url)


@user_passes_test(check_user)
def ledenlijst(request, speltak='wachtlijst'):
    if speltak == 'wachtlijst':
        leden = Lid.objects.filter(speltak=speltak).order_by('aanmeld_datum')
    else:
        leden = Lid.objects.filter(speltak=speltak)
    return render(request, 'ledenlijst.html', {'leden': leden, 'speltak': speltak, 'speltakken': Lid.LIJST_CHOICES})


class LidUpdateView(UserPassesTestMixin, UpdateView):
    model = Lid
    template_name = 'edit_lid.html'
    form_class = forms.LidForm

    def get_form(self, form_class=None):
        form = super(LidUpdateView, self).get_form(form_class)

        # Make the form read-only when user has no change permissions
        if not self.request.user.has_perm('LedenAdministratie.change_lid'):
            for name, field in form.fields.items():
                field.widget.attrs['disabled'] = True
        return form

    def test_func(self):
        return check_user(self.request.user)

    def get_success_url(self):
        url = "%s%s/" %(reverse_lazy('ledenlijst'), self.object.speltak)
        return url

    def form_valid(self, form):
        subject = 'Update ledenlijst van scouting St Ansfridus'
        body = render_to_string('edit_lid_email.html', context={'lid': form.instance, 'oldlid': form.initial})
        send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER, recipient_list=settings.EMAIL_RECIPIENTS_UPDATE)
        return super(LidUpdateView, self).form_valid(form)


class LidCreateView(UserPassesTestMixin, CreateView):
    model = Lid
    template_name = 'edit_lid.html'
    success_url = reverse_lazy('ledenlijst')
    form_class = forms.LidForm

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change

    def get_success_url(self):
        url = "%s%s/" % (reverse_lazy('ledenlijst'), self.object.speltak)
        return url

class LidAanmeldView(CreateView):
    model = Lid
    form_class = forms.LidCaptchaForm
    template_name = 'aanmelden_lid.html'
    success_url = reverse_lazy('aanmelden_ok')

    def form_valid(self, form):
        # Send an e-mail to 'bestuur'
        subject = 'Nieuwe aanmelding St. Ansfridus ontvangen'
        body = render_to_string('aanmelden_email.html', context={'lid': form.instance})
        send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER, recipient_list=settings.EMAIL_RECIPIENTS_NEW)

        # Send a confirmation e-mail to the user
        subject = 'Bevestiging aanmelding St. Ansfridus'
        body = render_to_string('aanmelden_email_user.html', context={'lid': form.instance})
        send_mail(subject=subject, message=body, from_email=settings.EMAIL_SENDER,
                  recipient_list=[form.instance.email_address])

        return super(LidAanmeldView, self).form_valid(form)


def aanmelden_ok(request):
    return render(request, 'aanmelden_ok.html')


class LidDeleteView(UserPassesTestMixin, DeleteView):
    model = Lid
    success_url = reverse_lazy('ledenlijst')
    template_name = 'delete_lid.html'
    fields = ['fist_name', 'last_name']

    def test_func(self):
        can_change = self.request.user.has_perm('LedenAdministratie.change_lid')
        return check_user(self.request.user) and can_change
