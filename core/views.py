from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.datastructures import MultiValueDictKeyError
from django.views import View
from django.views.generic import ListView, TemplateView
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView

from .forms import CreateArticleForm, FeedbackForm
from .models import *
from .utils import CorrelationTools

# Create your views here.


class ShowHome(ListView):
    model = Article
    queryset = Article.objects.all()[:3]
    template_name = "index.html"
    context_object_name = "articles"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Corrila - Free Online Data Correlation"
        context[
            "description_data"
        ] = "Corrila provides free online tools for data correlation. Choose the type of correlation coefficient: Pearson, Spearman or Kendall and get the results without having to download additional software."
        return context


class ShowAbout(TemplateView):
    template_name = "about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "About us - Corrila"
        return context


class ShowArticles(ListView):
    paginate_by = 2
    model = Article
    context_object_name = "articles"
    template_name = "articles.html"
    extra_context = {"title": "Articles - Corrila"}


class ShowArticlePage(View):
    template = "articles-page.html"

    def get(self, request, article_slug):
        article = get_object_or_404(Article, slug=article_slug)
        content = {"title": f"{article.title} - Corrila", "article": article}

        return render(request, self.template, content)


class ShowCorrelation(View):
    content = {"title": "Correlate data"}
    template = "correlate.html"

    def get(self, request):
        return render(request, self.template, self.content)

    def post(self, request):
        error_url = reverse("error")
        try:
            file = request.FILES["excel_file"]
        except MultiValueDictKeyError:
            # Redirect the user to the desired URL or display an error message
            message = "Error: File upload failed - maybe you forgot to upload it"
            return HttpResponseRedirect(f"{error_url}?message={message}")

        # Default limit for non-authenticated users
        file_size_limit = settings.NON_AUTHENTICATED_FILE_SIZE_LIMIT
        if request.user.is_authenticated:
            # Limit for authenticated users
            file_size_limit = settings.AUTHENTICATED_FILE_SIZE_LIMIT

        if file.size > file_size_limit:
            # Redirect the user to the desired URL or display an error message
            message = "Error: File upload failed max size exceeded for non-registered users 10 mb, for registered ones 20 mb"
            return HttpResponseRedirect(f"{error_url}?message={message}")

        high_choice = False
        low_choice = False

        try:
            if request.POST.get("pearson", False) == "on":
                correlaton_type_chosen = "pearson"
            if request.POST.get("spearman", False) == "on":
                correlaton_type_chosen = "spearman"
            if request.POST.get("kendall", False) == "on":
                correlaton_type_chosen = "kendall"

            if request.POST.get("high", False) == "on":
                high_choice = True
            if request.POST.get("low", False) == "on":
                low_choice = True

            correlator = CorrelationTools()
            correlator.filter_low_high_corr(file, method_chosen=correlaton_type_chosen)

            if request.user.is_authenticated:
                title = request.POST.get("title", False)
                if low_choice:
                    low = correlator.get_low_corr()
                else:
                    low = "Low correlation range has not been chosen"

                if high_choice:
                    high = correlator.get_high_corr()
                else:
                    high = "High correlation range has not been chosen"

                Report.objects.create(
                    title=title,
                    correlaton_type=correlaton_type_chosen,
                    low_correlaton_result=low,
                    high_correlaton_result=high,
                    author=request.user,
                )
                content = {
                    "title": title,
                    "correlaton_type": correlaton_type_chosen,
                    "low_correlaton_result": low,
                    "high_correlaton_result": high,
                    "author": request.user.username,
                }
                return render(request, "report.html", content)
            else:
                if low_choice:
                    low = correlator.get_low_corr()
                else:
                    low = "Low correlation range has not been chosen"

                if high_choice:
                    high = correlator.get_high_corr()
                else:
                    high = "High correlation range has not been chosen"

                content = {
                    "correlaton_type": correlaton_type_chosen,
                    "low_correlaton_result": low,
                    "high_correlaton_result": high,
                }
                return render(request, "report.html", content)
        except ValueError:
            # Redirect the user to the error page with the specific error message
            message = "I seems like you are trying to upload incorrect file"
            return HttpResponseRedirect(f"{error_url}?message={message}")


class FeedbackFormView(CreateView):
    template_name = "submit-feedback.html"
    form_class = FeedbackForm
    success_url = reverse_lazy("success")

    def form_valid(self, form):
        form.save()
        return super().form_valid(form)


class FeedSuccessbackFormView(TemplateView):
    template_name = "success-feedback.html"


def error_view(request):
    """
    A view function to render an error page with an optional error message.

    Parameters:
        request (HttpRequest): The request object passed by Django.

    Returns:
        HttpResponse: A response containing the rendered error.html template.

    Example Usage:
        # In your urls.py, add the following URL pattern to map to this view:
        path('error/', error_view, name='error')
    """
    message = request.GET.get("message", "")
    context = {"message": message}
    return render(request, "error.html", context)


class CreateArticleView(LoginRequiredMixin, CreateView):
    model = Article
    form_class = CreateArticleForm
    template_name = "create-article.html"
    success_url = reverse_lazy("article")

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()
