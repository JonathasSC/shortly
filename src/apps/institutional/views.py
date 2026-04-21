from django.shortcuts import render
from django.views import View

from apps.billing.models import Plan


class AboutUsView(View):
    def get(self, request):
        return render(request, "institutional/about-us.html")


class PrivacyPolicy(View):
    def get(self, request):
        return render(request, "institutional/privacy-policy.html")


class TermsOfUse(View):
    def get(self, request):
        plans = Plan.objects.all().order_by("price")
        return render(request, "institutional/terms-of-use.html", {"plans": plans})

