import requests
from io import BytesIO
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from apps.account.models import User, UserProfile


class AvatarS3FlowTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="test_user_s3_v2",
            email="test_s3_v2@example.com",
            password="testpassword123"
        )
        self.client = Client()
        self.client.force_login(self.user)

        # Criar uma imagem simples em memória para o teste
        image_io = BytesIO()
        image = Image.new("RGB", (100, 100), color="blue")
        image.save(image_io, format="JPEG")
        image_io.seek(0)
        
        self.avatar_file = SimpleUploadedFile(
            name="test_avatar.jpg",
            content=image_io.read(),
            content_type="image/jpeg"
        )

    def test_complete_avatar_flow(self):
        print("\n--- INICIANDO TESTE DE FLUXO S3 REAL ---")
        
        # 1. Garantir que o perfil existe
        profile, created = UserProfile.objects.get_or_create(user=self.user)
        
        # 2. Simular upload no Backend
        print(f"[Backend] Fazendo upload do avatar para: {profile.avatar.storage.__class__.__name__}")
        profile.avatar.save(f"test_avatar_{self.user.id}.jpg", self.avatar_file, save=True)
        
        # 3. Verificar se o arquivo foi salvo e tem URL
        self.assertTrue(profile.avatar.name.startswith("avatars/"))
        s3_url = profile.avatar.url
        print(f"[Backend] URL Assinada gerada: {s3_url[:120]}...")

        # 4. Testar a View de Redirecionamento do Django (Controle de Acesso)
        avatar_view_url = reverse('account:avatar_view', kwargs={'user_id': self.user.id})
        print(f"[Client] Testando View de Acesso: {avatar_view_url}")
        
        response = self.client.get(avatar_view_url)
        
        # Deve retornar um redirecionamento (302) para o S3
        self.assertEqual(response.status_code, 302)
        target_s3_url = response.url
        
        # 5. Validar Acesso Real ao S3 (Simulando o Navegador do Cliente)
        # Verificamos se a URL contém amazonaws ou o nome do seu bucket
        if "s3" in target_s3_url or "shortly-storage-prod" in target_s3_url:
            print("[Client] Validando se a URL assinada é acessível via HTTP GET...")
            try:
                # O timeout é importante em testes de rede
                s3_response = requests.get(target_s3_url, timeout=15)
                
                if s3_response.status_code == 200:
                    print(f"[SUCCESS] Imagem acessível pelo cliente! (HTTP 200)")
                    print(f"[SUCCESS] Content-Type: {s3_response.headers.get('Content-Type')}")
                else:
                    print(f"[FAILURE] S3 negou acesso: {s3_response.status_code}")
                    print(f"URL tentada: {target_s3_url}")
                    print(f"Detalhes do erro S3: {s3_response.text}")
                
                self.assertEqual(s3_response.status_code, 200)
                self.assertIn("image/", s3_response.headers.get("Content-Type", "").lower())
            except Exception as e:
                print(f"[ERROR] Falha de rede ao conectar ao S3: {str(e)}")
                raise e
        else:
            print(f"[WARNING] O storage atual ({profile.avatar.storage.__class__.__name__}) não parece ser S3. URL: {target_s3_url}")

        print("--- TESTE FINALIZADO ---")
