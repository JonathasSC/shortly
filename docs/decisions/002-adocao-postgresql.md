## Adoção de PostgreSQL
Número do ADR: 003
Data: 2025-08-18
Responsável: Jonathas dos Santos Cardoso
Status: Aceita

--- 

### 🧾 Contexto
Precisamos escolher um banco de dados relacional para o projeto.  
O Django suporta diversos bancos (SQLite, MySQL, PostgreSQL, Oracle), mas cada um tem pontos fortes e fracos.  
O sistema requer **alta confiabilidade, recursos avançados e escalabilidade**.

### ✅ Decisão
Optamos pelo **PostgreSQL** como banco de dados principal do projeto.

### 🎯 Consequências
- **Positivas**
  - Recursos avançados (JSONB, arrays, índices GIN/GiST).
  - Melhor suporte a consultas complexas e performance.
  - Estabilidade e maturidade reconhecidas no mercado.
  - Comunidade forte e bem documentada.
- **Negativas**
  - Mais pesado que SQLite (não indicado para prototipagem simples).
  - Necessidade de configuração e manutenção mais cuidadosa.

### 🔄 Alternativas Consideradas
- **SQLite**: simples, mas não atende em produção.
- **MySQL/MariaDB**: bons, mas menor suporte a recursos avançados e necessidade de licença.
- **Oracle**: descartado pelo custo de licenciamento.

### 📌 Status
**Aceita** — PostgreSQL será o banco de dados oficial do projeto.
