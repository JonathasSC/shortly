from apps.account.dtos.create_user_dto import CreateUserDTO
from apps.account.models import User


class CreateUserService:
    @staticmethod
    def execute(dto: CreateUserDTO) -> User:
        return User.objects.create(
            username=dto.username,
            email=dto.email,
            password=dto.password
        )
