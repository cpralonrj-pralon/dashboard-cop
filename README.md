# 📊 Dashboard de Produtividade — COP Rede

Dashboard Streamlit multi-perfil para análise de produtividade, indicadores
operacionais e **certificação de analistas** da equipe COP Rede.

O sistema identifica o usuário logado (analista, líder, coordenador,
sub-administrador ou super-admin) e exibe automaticamente apenas os dados,
abas e KPIs do seu escopo.

---

## Funcionalidades principais

### Upload e ingestão
- **Upload único** — uma planilha alimenta todas as abas
- Suporte a múltiplas fontes: Produtividade Analítica, Indicadores
  Empresarial, Indicadores Residencial, ETIT por Evento, DPA Oficial,
  Fechamento TOA x SIR, Chat TOA, etc.
- Filtros automáticos por mês, setor (Empresarial / Residencial) e analista

### Visões e KPIs
- **Highlights** — cartões executivos com volumes, médias, DPA e status
  de certificação do analista logado
- **Rankings** — Volume Total, Média Diária e DPA
- **Evolução diária** — gráficos de volume e produtividade ao longo do tempo
- **Composição de volume** — breakdown por tipo de atividade
  (NM, SGO, OSS, RAL, TOA, Telefonia, etc.)
- **Indicadores Empresarial** — ETIT por Evento por analista
- **Indicadores Residencial** — ETIT Fibra HFC, ETIT GPON,
  **Assertividade Acionamento Fibra HFC** e Assertividade GPON
- **Líderes** — visão consolidada por líder, com grid responsivo
  (até 4 cartões por linha)
- **Visão individual** — selecione um analista para ver seus dados em detalhe
- **Export CSV** — todos os dados e a aba de certificação podem ser baixados

---

## ✅ Certificação de Analistas

A certificação é avaliada automaticamente em duas dimensões:

### Residencial (analistas do Luiz, Vinícius e Nelson Residencial)
- **ETIT Fibra HFC** ≥ 90%
- **DPA Oficial** ≥ 90% (alerta entre 85% e 89,99%)
- **Média de Assertividade Acionamento (HFC + GPON)** ≥ 85%

### Empresarial (analistas do Patrick, Alexandre, Thiago Paroli e Nelson Empresarial)
- **ETIT por Evento** ≥ 90%
- **DPA Oficial** ≥ 90% (alerta entre 85% e 89,99%)

### Status possíveis
| Status | Significado |
|--------|-------------|
| 🟢 ✅ Certificando | Todos os indicadores dentro da meta |
| 🟡 ⚠️ Certificando (DPA fora) | ETIT/Assertividade OK, mas DPA entre 85% e 89,99% |
| 🔴 ❌ NÃO está Certificando | ETIT abaixo de 90% **ou** DPA abaixo de 85% |

> **Indicadores sem dados** são tratados como **dentro da meta** e
> sinalizados como tal na coluna *Observação* da aba administrativa.

---

## 👤 Perfis de acesso

| Perfil | Escopo |
|--------|--------|
| **Analista** | Apenas seus próprios dados; vê seu status de certificação nos Highlights |
| **Líder** | Sua equipe |
| **Coordenador (Luiz / Vinícius)** | Analistas Residenciais sob sua coordenação (setor travado em RESIDENCIAL) |
| **Sub-admin Empresarial (Patrick / Alexandre / Thiago Paroli)** | Sua coordenação (setor travado em EMPRESARIAL) |
| **Pralon** | Residencial (Luiz + Vinícius) + Nelson Residencial |
| **Evandro** | Empresarial (Patrick + Alexandre + Thiago Paroli) + Nelson Empresarial |
| **Nelson (Res / Emp)** | Toda a sua equipe |
| **Super-admin** | Visão completa de todos os setores |

Cada perfil administrativo possui a aba **✅ Analista Certificado**, que
lista o status de certificação de cada analista do seu escopo, com:

- KPIs: Total de analistas, 🟢 Certificando, 🟡 Em alerta, 🔴 Não certificando,
  ⚪ Sem segmento, **% Certificando**
- Filtros por situação e segmento
- Tabela ordenada dos piores aos melhores
- Export CSV

---

## Como rodar

```bash
# Criar venv
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Instalar dependências
pip install -r requirements.txt

# Rodar
streamlit run app.py
```

---

## Estrutura

```
├── app.py                 # Dashboard principal (abas, perfis, certificação)
├── src/
│   ├── config.py          # Equipe, colunas, escopos, indicadores
│   └── processors.py      # Carregamento e processamento das fontes
├── data/                  # Planilhas de exemplo
├── requirements.txt
└── README.md
```

---

## Ajustes comuns

- Equipe e escopos: `EQUIPE`, `EQUIPE_IDS`, `COORD_ANALYSTS_MAP`,
  `PRALON_ANALYSTS`, `EVANDRO_ANALYSTS` em `src/config.py`
- Indicadores Residenciais exibidos: `RES_INDICADORES_FILTRO`,
  `RES_IND_LABELS`, `RES_IND_COLORS`
- Linha do header das planilhas: `HEADER_ROW` em `src/config.py`
- Nomes de abas aceitos em cada fonte: `*_SHEET_NAME_CANDIDATES`
