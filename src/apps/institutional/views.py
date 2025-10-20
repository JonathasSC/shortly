from django.shortcuts import render
from django.views import View


class AboutUsView(View):
    def get(self, request):
        return render(request, "institutional/about-us.html")


class PrivacyPolicy(View):
    def get(self, request):
        return render(request, "institutional/privacy-policy.html")

