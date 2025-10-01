# 🎯 O auxílio da Análise de Dados para clubes de futebol na contratação de jogadores

## 📋 Descrição

Projeto simples de análise de dados desenvolvido como auxílio sobre o **Trabalho de Conclusão de Curso (TCC)**, focado na identificação e avaliação de atacantes no futebol europeu através de metodologias científicas baseadas em Expected Goals (xG) e analytics avançados.

## 🔬 Metodologia Científica

## Inovações Propostas
1. **Score Multidimensional Ponderado**: Combinação de produção, eficiência e consistência
2. **Fator de Regularidade Otimizado**: Baseado em minutos jogados (não apenas jogos)
3. **Análise de Custo-Benefício por Liga**: Identificação de oportunidades de mercado
4. **Consolidação Inteligente**: Tratamento de transferências inter-ligas

## 📊 Resultados Principais

- **2.774 jogadores** analisados das 5 principais ligas europeias
- **222 atacantes qualificados** após filtros de relevância estatística
- **TOP 10 selecionados** com **68.6% superior** em performance vs mercado geral
- **100% dos selecionados** no percentil 90+ de qualidade

## 🛠️ Tecnologias Utilizadas

```python
# Principais bibliotecas
pandas>=1.3.0          # Manipulação de dados
numpy>=1.21.0           # Computação científica
matplotlib>=3.4.0       # Visualização
sqlalchemy>=1.4.0       # Banco de dados
understat>=0.1.0        # API de dados esportivos
```

## 🚀 Como Usar

### 1. Instalação
```bash
git clone https://github.com/Lipeeeh14/AnaliseDadosAtacantes.git
cd AnaliseDadosAtacantes
pip install -r requirements.txt
```

### 2. Configuração
```python
# Configurar conexão com banco (opcional)
# Os dados podem ser coletados diretamente via API
```

### 3. Execução
```bash
# Análise completa
python analise_final.py

# Saídas geradas:
# - 5 dashboards em PNG
# - Relatório executivo
# - CSV com shortlist final
```

## 📈 Outputs do Sistema

### Dashboards Gerados
1. **Matriz de Decisão Estratégica** - Visualização de oportunidades
2. **Perfil TOP 5** - Análise radar dos melhores atacantes
3. **Comparativo de Performance** - Impacto vs mercado geral
4. **Análise por Liga** - Oportunidades de custo-benefício
5. **Relatório Executivo** - Síntese para tomada de decisão

### Arquivos de Dados
- `shortlist_atacantes_academica.csv` - TOP 10 selecionados
- Logs de execução com métricas estatísticas

## 🎯 Algoritmo de Scoring

```python
# Pesos otimizados para atacantes
Score_Base = (
    Gols_90min * 0.45 +              # Produção direta (45%)
    Impacto_Ofensivo * 0.25 +        # Contribuição total (25%)
    Eficiencia_Finalizacao * 0.20 +  # Qualidade técnica (20%)
    Key_Passes_90min * 0.10          # Criação de jogo (10%)
)

# Fator de confiabilidade (0.7x - 1.0x)
Score_Final = Score_Base * Fator_Regularidade
```

## 📚 Validação Científica

### Critérios de Qualificação
- **Mínimo 15 jogos** (relevância estatística)
- **Mínimo 900 minutos** (participação significativa)
- **Mínimo 0.2 gols/90min** (produtividade base)

### Resultados de Validação
- **68.6% superior** em gols/90min vs mercado
- **72.0% superior** em performance geral
- **Taxa de seleção**: 4.5% (10 de 222 qualificados)

## 🌍 Scope da Análise

### Ligas Cobertas
- **Premier League** (Inglaterra)
- **La Liga** (Espanha)
- **Bundesliga** (Alemanha)
- **Serie A** (Itália)
- **Ligue 1** (França)

### Temporada
- **2024**

## ⚠️ Disclaimer

Este sistema foi desenvolvido para **fins acadêmicos e de pesquisa**. Os fatores de custo-benefício são estimativas baseadas em percepção geral de mercado, não refletindo valores reais de transferência.

## 📖 Citação Acadêmica

```bibtex
@misc{sistema_recrutamento_2024,
  author = {[Luiz Felipe]},
  title = {O auxílio da Análise de Dados para clubes de futebol na contratação de jogadores},
  year = {2025},
  publisher = {GitHub},
  url = {https://github.com/Lipeeeh14/AnaliseDadosAtacantes}
}
```

## 🤝 Contribuições

Contribuições são bem-vindas! Este projeto segue os princípios de **ciência aberta** e **reprodutibilidade científica**.