from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import (
    LoginView,
    PasswordResetConfirmView,
    PasswordResetView,
)
from django.shortcuts import HttpResponse, get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic.edit import CreateView, DeleteView

from core.models import Article, Report

from .forms import *


class SignUpUser(CreateView):
    form_class = UserProfileCreationForm
    template_name = "sign-up.html"
    success_url = reverse_lazy("sign-in")

    def get_context_data(self, **kwargs):
        context = super(SignUpUser, self).get_context_data(**kwargs)
        context["title"] = "Sign-Up - Corrila"
        return context

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect("home")


class SignInUser(LoginView):
    form_class = CorrilaAutnenticationForm
    template_name = "sign-in.html"

    def get_context_data(self, **kwargs):
        context = super(SignInUser, self).get_context_data(**kwargs)
        context["title"] = "Sign-in - Corrila"
        return context

    def get_success_url(self):
        return reverse_lazy("home")


# TODO: You can use the default LogoutView from Django by passing the LOGOUT_REDIRECT_URL in the settings
#   No need to create a new view
def logout_user(request):
    logout(request)
    return redirect("sign-in")


# TODO: Could you use a DetailView here instead of a normal View?
#   It will manage for you get_object_or_404
#   And you can overload the context to add reports and articles
class ShowProfile(LoginRequiredMixin, UserPassesTestMixin, View):
    template = "profile.html"

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        reports = Report.objects.filter(author=user)
        articles = Article.objects.filter(author=user)
        content = {"title": f"Corrila Account",
                   "user": user, "reports": reports, "articles": articles}

        return render(request, self.template, content)

    # TODO: This function is used in other view. You can put it in a Mixin and reuse this Mixin
    def test_func(self):
        user_id = self.kwargs["user_id"]
        return self.request.user.id == int(user_id)


# TODO: Could you use a DetailView here instead of a normal View?
class ShowReport(LoginRequiredMixin, UserPassesTestMixin, View):
    template = "user-report.html"

    def get(self, request, report_id):
        report = get_object_or_404(Report, pk=report_id)
        content = {"title": f"Report - {report.title}", "report": report}

        return render(request, self.template, content)

    # TODO: This function is used in other view. You can put it in a Mixin and reuse this Mixin
    def test_func(self):
        reports = get_object_or_404(Report, pk=self.kwargs["report_id"])
        user_id = reports.author.pk
        return self.request.user.id == int(user_id)


class DeleteReport(DeleteView, LoginRequiredMixin):
    model = Report
    template_name = "delete-report.html"
    success_url = reverse_lazy("home")


class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomPasswordResetConfirmForm
