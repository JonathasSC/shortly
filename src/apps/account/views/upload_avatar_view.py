from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.contrib import messages

from apps.account.models import UserProfile
from apps.account.services.image_processor_service import ImageProcessor
from apps.account.services.image_validator_service import ImageValidator

class UploadAvatarView(LoginRequiredMixin, View):

    http_method_names = ["post"]

    def post(self, request):

        image = request.FILES.get("image")

        if not image:
            messages.error(request, "Image is required.")
            return redirect("account:profile")

        try:

            ImageValidator.validate_extension(image.name)
            ImageValidator.validate_image(image)

            processor = ImageProcessor()

            processed_image = processor.resize(image)

            profile, _ = UserProfile.objects.get_or_create(
                user=request.user
            )

            profile.avatar.save(
                image.name,
                processed_image,
                save=True
            )

            messages.success(request, "Avatar updated successfully.")

        except ValueError as error:

            messages.error(request, str(error))

        return redirect("account:profile")
