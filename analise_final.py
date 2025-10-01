import asyncio
from sqlalchemy import inspect, text
import aiohttp
from understat import Understat
import pandas as pd
from sqlalchemy import create_engine
import matplotlib.pyplot as plt
import numpy as np

async def get_league_player_stats(league: str, season: int):
    async with aiohttp.ClientSession() as session:
        understat = Understat(session)
        players = await understat.get_league_players(league, season)
        print(f"[{league}] Total de jogadores encontrados: {len(players)}")
        all_stats = []
        for player in players:
            try:
                id = int(player['id'])
                player_name = player['player_name']
                team_title = player['team_title']
                position = player['position']
                total_xg = float(player['xG'])
                total_xa = float(player['xA'])
                goals = int(player['goals'])
                assists = int(player['assists'])
                shots = int(player['shots'])
                key_passes = int(player['key_passes'])
                minutes = int(player['time'])
                games = int(player['games'])
                
                all_stats.append({
                    'Id': id,
                    'Nome': player_name,
                    'Time': team_title,
                    'Posição': position,
                    'Gols': goals,
                    'Assistências': assists,
                    'xG': round(total_xg, 2),
                    'xA': round(total_xa, 2),
                    'Finalizações': shots,
                    'Passes-chave': key_passes,
                    'Minutos': minutes,
                    'Jogos': games,
                    'Gols_90min': round(goals / (minutes / 90), 2) if minutes > 0 else 0,
                    'Assistências_90min': round(assists / (minutes / 90), 2) if minutes > 0 else 0,
                    'xG_90min': round(total_xg / (minutes / 90), 2) if minutes > 0 else 0,
                    'xA_90min': round(total_xa / (minutes / 90), 2) if minutes > 0 else 0,
                    'Shots_90min': round(shots / (minutes / 90), 2) if minutes > 0 else 0,
                    'Key_Passes_90min': round(key_passes / (minutes / 90), 2) if minutes > 0 else 0,
                    'Liga': league,
                    'Temporada': season
                })
            except Exception as e:
                print(f"Erro com {player_name}: {e}")
        return pd.DataFrame(all_stats)

leagues = ["Ligue_1", "epl", "La_Liga", "Bundesliga", "Serie_A"]
season = 2024

plt.style.use('default')
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 10

liga_colors = {
    'epl': 'red', 
    'La_Liga': 'orange', 
    'Bundesliga': 'green', 
    'Serie_A': 'blue', 
    'Ligue_1': 'purple'
}

engine = create_engine(
    "" # Adicionar a string de conexão com o SQL Server aqui
)

table_name = "estatisticas_understat"
inspector = inspect(engine)
table_exists = inspector.has_table(table_name)

if table_exists:
    with engine.connect() as conn:
        result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name} WHERE Temporada = {season}"))
        row_count = result.scalar()
        if row_count > 0:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} WHERE Temporada = {season}", con=engine)
        else:
            dfs = []
            for league in leagues:
                df_league = asyncio.run(get_league_player_stats(league, season))
                dfs.append(df_league)
            df = pd.concat(dfs, ignore_index=True)
            df.to_sql("estatisticas_understat", con=engine, if_exists="replace", index=False)
else:
    dfs = []
    for league in leagues:
        print(f"Coletando dados para {league}...")
        df_league = asyncio.run(get_league_player_stats(league, season))
        dfs.append(df_league)
    df = pd.concat(dfs, ignore_index=True)
    df.to_sql("estatisticas_understat", con=engine, if_exists="replace", index=False)


duplicatas_nome = df[df.duplicated(['Nome'], keep=False)]
if len(duplicatas_nome) > 0:
    for nome in duplicatas_nome['Nome'].unique():
        registros_jogador = df[df['Nome'] == nome]

    df_original = df.copy()
    
    df_grouped = df.groupby('Nome').agg({
        'Id': 'first',
        'Posição': 'first',
        'Time': lambda x: ', '.join(x.unique()),
        'Liga': lambda x: ', '.join(x.unique()),
        'Gols': 'sum',
        'Assistências': 'sum', 
        'xG': 'sum',
        'xA': 'sum',
        'Finalizações': 'sum',
        'Passes-chave': 'sum',
        'Minutos': 'sum',
        'Jogos': 'sum',
        'Temporada': 'first'
    }).reset_index()
    
    # Recalcular métricas por 90min
    df_grouped['Gols_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                       round(df_grouped['Gols'] / (df_grouped['Minutos'] / 90), 2), 0)
    df_grouped['Assistências_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                               round(df_grouped['Assistências'] / (df_grouped['Minutos'] / 90), 2), 0)
    df_grouped['xG_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                     round(df_grouped['xG'] / (df_grouped['Minutos'] / 90), 2), 0)
    df_grouped['xA_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                     round(df_grouped['xA'] / (df_grouped['Minutos'] / 90), 2), 0)
    df_grouped['Shots_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                        round(df_grouped['Finalizações'] / (df_grouped['Minutos'] / 90), 2), 0)
    df_grouped['Key_Passes_90min'] = np.where(df_grouped['Minutos'] > 0, 
                                             round(df_grouped['Passes-chave'] / (df_grouped['Minutos'] / 90), 2), 0)
       
    def determinar_liga_principal(row):
        if ',' in str(row['Liga']):
            jogador_original = df_original[df_original['Nome'] == row['Nome']]
            liga_principal = jogador_original.loc[jogador_original['Minutos'].idxmax(), 'Liga']
            return liga_principal
        return row['Liga']
    
    df_grouped['Liga'] = df_grouped.apply(determinar_liga_principal, axis=1)
    
    df = df_grouped

def aplicar_filtros_realistas(df):
    df_fwd = df[df['Posição'].str.contains('F', na=False)].copy()
    
    df_fwd = df_fwd[
        (df_fwd['Jogos'] >= 15) &
        (df_fwd['Minutos'] >= 900) &
        (df_fwd['Gols_90min'] >= 0.2)
    ]
    
    return df_fwd

clubes_grandes = [
    "Real Madrid", "Bayern Munich", "Manchester City", "Paris Saint Germain", "Barcelona",
    "Liverpool", "Atletico Madrid", "Manchester United", "Chelsea", "Borussia Dortmund",
    "Juventus", "Arsenal", "Roma", "Inter", "Sevilla", "Benfica", "Bayer Leverkusen",
    "Tottenham", "Porto", "Napoli"
]

df_fwd = aplicar_filtros_realistas(df)
df_fwd = df_fwd[~df_fwd['Time'].isin(clubes_grandes)]

def calcular_score_ponderado(df):
    df['Eficiencia_Finalizacao'] = df['Gols'] / df['xG'].replace(0, 0.1)
    
    minutos_max = df['Minutos'].max()
    df['Fator_Regularidade'] = np.clip(np.sqrt(df['Minutos'] / minutos_max), 0.7, 1.0)
    
    df['Impacto_Ofensivo'] = df['Gols_90min'] + (df['Assistências_90min'] * 0.8)
    
    df['Score_Base'] = (
        df['Gols_90min'] * 0.45 +
        df['Impacto_Ofensivo'] * 0.25 +
        df['Eficiencia_Finalizacao'] * 0.20 +
        df['Key_Passes_90min'] * 0.10
    )
    
    df['Score_Ponderado'] = df['Score_Base'] * df['Fator_Regularidade']
    df['Versatilidade'] = (df['Gols_90min'] > 0.3) & (df['Assistências_90min'] > 0.1)
    df['Nivel_Risco'] = pd.cut(df['Jogos'], bins=[0, 20, 28, 35, 50], 
                              labels=['Alto', 'Médio', 'Baixo', 'Muito Baixo'])
    
    return df

def analisar_custo_beneficio_balanceado(df):
    valor_liga = {
        'epl': 1.0,        # Premier League (referência estimada - mais caro)
        'La_Liga': 0.95,   # La Liga (estimativa - próxima em valor)
        'Bundesliga': 0.90, # Bundesliga (estimativa - liga competitiva)
        'Serie_A': 0.85,   # Serie A (estimativa - menor valorização)
        'Ligue_1': 0.80    # Ligue 1 (estimativa - oportunidades de valor)
    }
    
    df['Fator_Liga'] = df['Liga'].map(valor_liga).fillna(0.85)
    df['Custo_Beneficio'] = df['Score_Ponderado'] / df['Fator_Liga']
    
    return df

df_fwd = calcular_score_ponderado(df_fwd)
df_fwd = analisar_custo_beneficio_balanceado(df_fwd)



def criar_shortlist_final(df_fwd, n_jogadores=10):
    shortlist = df_fwd.sort_values('Score_Ponderado', ascending=False).head(n_jogadores)
    
    for liga in shortlist['Liga'].value_counts().index:
        pass
    
    return shortlist

shortlist = criar_shortlist_final(df_fwd)

top10_columns = ['Nome', 'Time', 'Liga', 'Jogos', 'Gols_90min', 'Score_Ponderado', 'Fator_Regularidade', 'Custo_Beneficio']



def criar_dashboard_matriz_decisao(shortlist):
    plt.figure(figsize=(16, 10))
    
    colors = [liga_colors.get(liga, 'gray') for liga in shortlist['Liga']]
    sizes = shortlist['Jogos'] * 4
    
    plt.scatter(shortlist['Score_Ponderado'], shortlist['Custo_Beneficio'], 
                         c=colors, s=sizes, alpha=0.8, edgecolors='black', linewidth=1.5)
    score_medio = shortlist['Score_Ponderado'].median()
    cb_medio = shortlist['Custo_Beneficio'].median()
    
    plt.axhline(y=cb_medio, color='gray', linestyle='--', alpha=0.6, linewidth=2)
    plt.axvline(x=score_medio, color='gray', linestyle='--', alpha=0.6, linewidth=2)
    top10 = shortlist.head(10)
    for i, (_, jogador) in enumerate(top10.iterrows()):
        info_text = (f"{jogador['Nome'][:30]}\n"
                    f"{jogador['Time'][:15]}\n"
                    f"G: {jogador['Gols_90min']:.2f}/90min\n"
                    f"A: {jogador['Assistências_90min']:.2f}/90min")
        offset_x = 15 if i % 2 == 0 else -80
        offset_y = 15 + (i % 3) * 20
        
        plt.annotate(info_text, 
                    (jogador['Score_Ponderado'], jogador['Custo_Beneficio']), 
                    xytext=(offset_x, offset_y), textcoords='offset points', 
                    fontsize=8, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.4", 
                             facecolor="yellow" if i < 3 else "lightblue", 
                             alpha=0.9, edgecolor='black'),
                    arrowprops=dict(arrowstyle='->', color='black', alpha=0.7))
    plt.text(0.75, 0.25, 'ZONA PRIORITÁRIA\n* Pontuação Alta + Alto C/B\n(Alvos Principais)', 
             transform=plt.gca().transAxes, fontsize=11, fontweight='bold',
             bbox=dict(boxstyle="round", facecolor="lightgreen", alpha=0.8),
             ha='center', va='center')
    
    plt.text(0.30, 0.75, 'OPORTUNIDADES\n* Pontuação Média + Alto C/B\n(Avaliar Potencial)', 
             transform=plt.gca().transAxes, fontsize=11, fontweight='bold',
             bbox=dict(boxstyle="round", facecolor="lightyellow", alpha=0.8),
             ha='center', va='center')
    
    plt.xlabel('Pontuação Ponderada (Qualidade Técnica)', fontsize=14, fontweight='bold')
    plt.ylabel('Custo-Benefício (Oportunidade de Mercado)', fontsize=14, fontweight='bold')
    plt.title('MATRIZ DE DECISÃO ESTRATÉGICA\nFoco nos Top 10 Atacantes Identificados', 
              fontsize=16, fontweight='bold', pad=20)
    from matplotlib.lines import Line2D
    legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=color, 
                             markersize=10, label=liga.replace('_', ' ')) 
                      for liga, color in liga_colors.items()]
    plt.legend(handles=legend_elements, title="Liga de Origem", 
              loc='upper left', fontsize=10, title_fontsize=11)
    
    plt.grid(True, alpha=0.4, linestyle=':')
    plt.tight_layout()
    plt.savefig('01_matriz_decisao_jogadores.png', dpi=300, bbox_inches='tight')
    plt.close()

def criar_perfil_individual_top5(shortlist):
    fig, axes = plt.subplots(1, 5, figsize=(20, 8))
    
    top5 = shortlist.head(5)
    
    for idx, (i, jogador) in enumerate(top5.iterrows()):
        ax = axes[idx]
        metricas = ['Gols/90', 'Assist/90', 'Eficiência', 'Regularidade']
        valores = [
            jogador['Gols_90min'],
            jogador['Assistências_90min'], 
            jogador['Eficiencia_Finalizacao'],
            jogador['Fator_Regularidade']
        ]
        valores_norm = []
        max_vals = [1.2, 0.8, 2.0, 1.0]
        for v, max_v in zip(valores, max_vals):
            valores_norm.append(min(v/max_v, 1.0))

        angles = np.linspace(0, 2 * np.pi, len(metricas), endpoint=False).tolist()
        valores_norm += valores_norm[:1]
        angles += angles[:1]
        cores_ranking = ['#FFD700', '#C0C0C0', '#CD7F32', '#4CAF50', '#2196F3']
        cor = cores_ranking[idx]
        
        ax.plot(angles, valores_norm, 'o-', linewidth=3, color=cor, markersize=8)
        ax.fill(angles, valores_norm, alpha=0.3, color=cor)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(metricas, fontsize=10, weight='bold')
        ax.set_ylim(0, 1)
        ax.set_yticks([0.25, 0.5, 0.75, 1.0])
        ax.set_yticklabels(['25%', '50%', '75%', '100%'], fontsize=9)
        ax.grid(True, alpha=0.4)
        nome_curto = jogador['Nome'].split()[0] if len(jogador['Nome'].split()) > 1 else jogador['Nome'][:12]
        titulo = (f"#{idx+1}º {nome_curto}\n"
                 f"{jogador['Liga'].replace('_', ' ')}\n"
                 f"Pontuação: {jogador['Score_Ponderado']:.2f}\n"
                 f"{jogador['Jogos']} jogos em 2024")
        
        ax.set_title(titulo, fontsize=12, fontweight='bold', pad=20)
        ax.patch.set_facecolor(cor)
        ax.patch.set_alpha(0.1)
    
    plt.suptitle('TOP 5 ATACANTES - PERFIL DE DESEMPENHO\nAnálise das Métricas Essenciais para Tomada de Decisão', 
                fontsize=16, fontweight='bold', y=0.95)
    plt.tight_layout(rect=[0, 0, 1, 0.92])
    plt.savefig('02_perfil_top5_jogadores.png', dpi=300, bbox_inches='tight')
    plt.close()

def criar_comparativo_jogadores(shortlist, df_fwd):
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    
    top10 = shortlist.head(10)
    media_mercado = df_fwd['Gols_90min'].mean()
    cores = ['gold' if score > media_mercado*1.5 else 
             'lightgreen' if score > media_mercado*1.2 else 
             'orange' for score in top10['Gols_90min']]
    
    bars = ax.barh(range(len(top10)), top10['Gols_90min'], 
                   color=cores, alpha=0.8, edgecolor='black', linewidth=2)
    ax.axvline(x=media_mercado, color='red', linestyle='--', linewidth=3, 
               label=f'MÉDIA DO MERCADO: {media_mercado:.2f} gols/90min')
    labels = []
    for i, (_, jogador) in enumerate(top10.iterrows()):
        diferenca_pct = ((jogador['Gols_90min'] / media_mercado) - 1) * 100
        nome_curto = jogador['Nome'][:20] if len(jogador['Nome']) <= 20 else jogador['Nome'][:17] + "..."
        label = f"#{i+1} {nome_curto}\n{jogador['Liga'].replace('_', ' ')} | +{diferenca_pct:.0f}% vs mercado"
        labels.append(label)
    
    ax.set_yticks(range(len(top10)))
    ax.set_yticklabels(labels, fontsize=11)
    ax.set_xlabel('GOLS POR 90 MINUTOS', fontweight='bold', fontsize=14)
    for i, (bar, (_, jogador)) in enumerate(zip(bars, top10.iterrows())):
        width = bar.get_width()
        ax.text(width + 0.02, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', ha='left', va='center', fontweight='bold', fontsize=12)
    plt.title('🎯 IMPACTO DA ANÁLISE DE DADOS NO RECRUTAMENTO\n' +
             f'TOP 10 ATACANTES: {top10["Gols_90min"].mean():.2f} vs MERCADO: {media_mercado:.2f} gols/90min\n' +
             f'MELHORIA DE {((top10["Gols_90min"].mean() / media_mercado - 1) * 100):.0f}% NA PRODUTIVIDADE', 
             fontsize=18, fontweight='bold', pad=20)
    ax.legend(fontsize=12, loc='lower right')
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, max(top10['Gols_90min']) * 1.15)
    textstr = f'''VALIDAÇÃO CIENTÍFICA:
• Amostra analisada: {len(df_fwd):,} atacantes
• Taxa de seleção: {(len(shortlist)/len(df_fwd)*100):.1f}%
• Performance superior: +{((shortlist["Gols_90min"].mean() / media_mercado - 1) * 100):.0f}%'''
    
    props = dict(boxstyle='round', facecolor='lightblue', alpha=0.8)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig('03_comparativo_detalhado_jogadores.png', dpi=300, bbox_inches='tight')
    plt.close()

def criar_analise_mercado_ligas(shortlist, df_fwd):
    fig, ax = plt.subplots(1, 1, figsize=(16, 10))
    ligas_ordenadas = ['Ligue_1', 'Serie_A', 'Bundesliga', 'La_Liga', 'epl']
    nomes_ligas = ['Ligue 1\n(França)', 'Serie A\n(Itália)', 'Bundesliga\n(Alemanha)', 
                   'La Liga\n(Espanha)', 'Premier League\n(Inglaterra)']
    dados_liga = []
    for liga in ligas_ordenadas:
        shortlist_liga = shortlist[shortlist['Liga'] == liga]
        mercado_liga = df_fwd[df_fwd['Liga'] == liga]
        
        if len(shortlist_liga) > 0:
            cb_medio = shortlist_liga['Custo_Beneficio'].mean()
            taxa_selecao = (len(shortlist_liga) / len(mercado_liga)) * 100 if len(mercado_liga) > 0 else 0
            score_medio = shortlist_liga['Score_Ponderado'].mean()
            
            dados_liga.append({
                'liga': liga,
                'nome': nomes_ligas[ligas_ordenadas.index(liga)],
                'cb': cb_medio,
                'taxa': taxa_selecao,
                'score': score_medio,
                'jogadores': len(shortlist_liga)
            })
    dados_liga.sort(key=lambda x: x['cb'], reverse=True)
    cores = []
    for dado in dados_liga:
        if dado['cb'] > 0.95:
            cores.append('gold')
        elif dado['cb'] > 0.90:
            cores.append('lightgreen')
        else:
            cores.append('orange')
    y_pos = range(len(dados_liga))
    valores_cb = [d['cb'] for d in dados_liga]
    
    bars = ax.barh(y_pos, valores_cb, color=cores, alpha=0.8, edgecolor='black', linewidth=2)
    labels = []
    for dado in dados_liga:
        label = f"{dado['nome']}\n{dado['jogadores']} jogadores | Taxa: {dado['taxa']:.1f}%"
        labels.append(label)
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=12)
    ax.set_xlabel('CUSTO-BENEFÍCIO MÉDIO (Pontuação/Fator Liga)', fontweight='bold', fontsize=14)
    
    for i, (bar, dado) in enumerate(zip(bars, dados_liga)):
        width = bar.get_width()
        ax.text(width + 0.05, bar.get_y() + bar.get_height()/2, 
                f'{width:.2f}', ha='left', va='center', fontweight='bold', fontsize=13)
   
    melhor_liga = dados_liga[0]['nome'].split('\n')[0]
    
    plt.title('ANÁLISE DE OPORTUNIDADES DE MERCADO POR LIGA\n' +
             f'MELHOR CUSTO-BENEFÍCIO: {melhor_liga} ({dados_liga[0]["cb"]:.2f})\n', 
             fontsize=18, fontweight='bold', pad=20)
    
    ax.grid(True, alpha=0.3, axis='x')
    ax.set_xlim(0, max(valores_cb) * 1.15)
    
    textstr = f'''INSIGHTS ESTRATÉGICOS:
        • {dados_liga[0]['nome'].split()[0]}: Melhor C/B ({dados_liga[0]['cb']:.2f}) - PRIORIDADE
        • {dados_liga[1]['nome'].split()[0]}: 2ª melhor ({dados_liga[1]['cb']:.2f}) - Alternativa
        • Total analisado: {len(df_fwd):,} atacantes de 5 ligas'''
    
    props = dict(boxstyle='round', facecolor='lightcyan', alpha=0.9)
    ax.text(0.02, 0.98, textstr, transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=props)
    
    plt.tight_layout()
    plt.savefig('04_analise_mercado_ligas.png', dpi=300, bbox_inches='tight')
    plt.close()

def criar_relatorio_executivo_simples(shortlist):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), gridspec_kw={'height_ratios': [1, 3]})
    ax1.axis('off')
    
    kpis = {
        'Atacantes Analisados': len(df_fwd),
        'Lista Final': len(shortlist),
        'Pontuação Média': f"{shortlist['Score_Ponderado'].mean():.2f}",
        'Melhor C/B': f"{shortlist['Custo_Beneficio'].max():.2f}",
        'Ligas Cobertas': shortlist['Liga'].nunique()
    }
    
    kpi_text = "  •  ".join([f"{k}: {v}" for k, v in kpis.items()])
    
    ax1.text(0.5, 0.5, f"INDICADORES PRINCIPAIS\n{kpi_text}", 
             transform=ax1.transAxes, fontsize=12, fontweight='bold', 
             ha='center', va='center',
             bbox=dict(boxstyle="round,pad=0.8", facecolor="lightblue", alpha=0.8))
    ax2.axis('off')
    
    table_data = []
    for idx, (_, jogador) in enumerate(shortlist.head(10).iterrows(), 1):
        table_data.append([
            f"{idx}º",
            jogador['Nome'][:16],
            jogador['Time'].split()[0] if len(jogador['Time']) > 15 else jogador['Time'],
            f"{jogador['Gols_90min']:.2f}",
            f"{jogador['Assistências_90min']:.2f}",
            f"{jogador['Score_Ponderado']:.2f}",
            f"{jogador['Custo_Beneficio']:.2f}"
        ])
    
    table = ax2.table(cellText=table_data,
                     colLabels=['Pos', 'Jogador', 'Clube', 'Gols/90', 
                               'Assist/90', 'Pontuação', 'C/B'],
                     cellLoc='center', loc='center',
                     bbox=[0, 0, 1, 1])
    
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    for (i, j), cell in table.get_celld().items():
        if i == 0:
            cell.set_text_props(weight='bold', color='white')
            cell.set_facecolor('#2C3E50')
        else:
            cell.set_facecolor('#F8F8FF' if i % 2 == 0 else 'white')
        cell.set_edgecolor('black')
        cell.set_linewidth(0.8)
    
    plt.suptitle('RELATÓRIO EXECUTIVO - ANÁLISE DE DADOS PARA RECRUTAMENTO', 
                 fontsize=16, fontweight='bold', y=0.95)
    plt.savefig('relatorio_executivo_academico.png', dpi=300, bbox_inches='tight')
    plt.close()


criar_dashboard_matriz_decisao(shortlist)
criar_perfil_individual_top5(shortlist)
criar_comparativo_jogadores(shortlist, df_fwd)
criar_analise_mercado_ligas(shortlist, df_fwd)

criar_relatorio_executivo_simples(shortlist)

shortlist.to_csv('shortlist_atacantes_academica.csv', index=False)