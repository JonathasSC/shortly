## Organização de Aplicativos Django
Número do ADR: 001
Data: 2025-08-18
Responsável: Jonathas dos Santos Cardoso
Status: Aceita

---

### 🧾 Contexto
Durante o desenvolvimento do sistema, foi necessário definir como os aplicativos Django seriam organizados.  
Existem diversas abordagens possíveis, como:
- Organização por **feature** (cada app corresponde a uma funcionalidade).
- Organização clássica (apps genéricos + específicos do projeto).
- Organização inspirada por **domínio de negócio (DDD)**.

Como o sistema terá crescimento contínuo e pretensão de longividade e múltiplos domínios de negócio, foi avaliado que a arquitetura deveria privilegiar **clareza**, **isolamento** e **escalabilidade**.

---

### ✅ Decisão
Optamos por adotar a **organização de aplicativos Django baseada em Domínios (Domain-Driven Design - DDD)**.  
Isso significa que cada app do Django representará um domínio do negócio, e dentro de cada app serão organizadas as camadas de **entidades (models)**, **serviços (services/use cases)**, **repositórios** e **interfaces (views/api/serializers)**.

#### Critérios para decidir os apps por domínio

Você cria um novo app quando:
* O conjunto de regras de negócio é coeso → Ex.: "Financeiro" lida com faturas, boletos e cobranças.

* Complexidade → Se um módulo tende a crescer muito, isolar em um app ajuda a manter organizado.

**Exemplo de Estrutura:**
```
myproject/
  financeiro/
    models/          # entidades do domínio
    views/           # lógica de negócio
    tests/           # testes focados no domínio

```
---

### 🎯 Consequências
- **Positivas**
  - Cada domínio é isolado, facilitando manutenção e testes.
  - Facilita migração futura para microsserviços.
  - Escalável para times maiores.
  - Clareza no mapeamento entre o negócio e o código.

- **Negativas**
  - Exige maior disciplina na definição das fronteiras de cada domínio.
  - Pode gerar mais sobrecarga inicial de estruturação para domínios pequenos.

---

### 🔄 Alternativas Consideradas
- **Por Feature**: descartada, pois tende a misturar múltiplos domínios dentro de uma mesma feature.
- **Por Setor da Empresa**: descartada, pois a estrutura organizacional pode mudar, afetando diretamente a arquitetura.
- **Clássica (apps genéricos + específicos)**: descartada, pois não fornece isolamento claro entre domínios de negócio.

### 📌 Status
**Aceita**
