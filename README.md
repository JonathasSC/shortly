# 🚀 Shortly

**Shortly** é uma plataforma moderna de **encurtamento de links** que permite criar, gerenciar e acompanhar URLs curtas de forma simples e eficiente.  
Ela foi desenvolvida para oferecer praticidade, controle e métricas em tempo real — ideal para criadores de conteúdo, empresas e profissionais que desejam otimizar a forma como compartilham seus links.

---

## 🌐 Acesso à Plataforma

Você pode acessar o Shortly diretamente em:

👉 **[https://sh0rtly.com](https://sh0rtly.com)**  

Através do painel, é possível:
- Criar e editar links curtos personalizados;  
- Acompanhar estatísticas de cliques e engajamento;  
- Gerenciar sua conta e créditos;  
- Adquirir créditos para continuar encurtando links.

---

## 💳 Formas de Compra

Atualmente, o **Shortly** utiliza o **Mercado Pago** como meio de pagamento oficial.  
Os usuários podem **comprar créditos** diretamente pela plataforma, que são automaticamente adicionados à carteira da conta após a aprovação do pagamento.

### 🔹 Como funciona a compra de créditos:

1. O usuário escolhe o valor desejado em créditos.  
2. O pagamento é processado de forma segura via **Mercado Pago**.  
3. Após a confirmação (webhook automático), os créditos são adicionados à **carteira digital (wallet)** do usuário dentro do Shortly.  
4. Os créditos podem ser usados para encurtar novos links ou acessar recursos premium.

---

## 🔒 Segurança

- Todos os pagamentos são validados com **assinatura digital (HMAC)** enviada pelo Mercado Pago.  
- O webhook do Shortly verifica a autenticidade de cada requisição antes de atualizar qualquer informação financeira.  
- As chaves de autenticação e tokens de API são armazenados com segurança em variáveis de ambiente (`.env`).

---

## 🧩 Integrações

- **Mercado Pago SDK** — responsável pela criação e validação de pagamentos.  
- **Sistema de Wallet interno** — gerencia os créditos e histórico de transações do usuário.  
- **Webhooks automáticos** — processam e validam o status de cada pagamento em tempo real.

---

## 📊 Roadmap Futuro

- Adição de **planos de assinatura mensais**; 
- Links customizáveis;

---

## 🧠 Sobre o Projeto

O Shortly foi desenvolvido com foco em **performance, segurança e escalabilidade**, utilizando **Django** no backend e integração direta com o **Mercado Pago** para automação de pagamentos. 

---

📩 **Contato e Suporte**  
Caso tenha dúvidas ou sugestões, entre em contato pelo e-mail:  
**suporte@sh0rtly.com**
