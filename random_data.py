import pandas as pd
import numpy as np
import random

np.random.seed(42)
random.seed(42)

neigh_path = 'data/neighborhoods.xlsx'
neigh_df = pd.read_excel(neigh_path)

# Cria dicionário Zona -> lista de bairros
zona_para_bairros = (
    neigh_df.groupby('Zona')['name_neighborhood']
    .apply(list)
    .to_dict()
)

zonas = list(zona_para_bairros.keys())

p_zonas = [0.35, 0.30, 0.25, 0.10]
ordem_zonas = ['Zona Norte', 'Zona Oeste', 'Zona Sul', 'Centro']
zonas = ordem_zonas

periodo = pd.date_range('2024-01-01', '2025-05-01', freq='MS')
amostra_mensal = 2000

sexos = ['Masculino', 'Feminino']
p_sexos = [0.48, 0.52]

faixas_etarias = ['16-24', '25-29', '30-39', '40-49', '50-59', '60+']
p_idade = [0.18, 0.12, 0.24, 0.18, 0.16, 0.12]

cores_raca = ['Branca', 'Parda', 'Preta', 'Amarela', 'Indígena']
p_raca = [0.46, 0.37, 0.14, 0.02, 0.01]

escolaridades = ['Sem instrução', 'Fundamental incompleto', 'Fundamental completo',
                 'Médio incompleto', 'Médio completo', 'Superior incompleto',
                 'Superior completo', 'Pós-graduação']
p_esc = [0.04, 0.10, 0.11, 0.08, 0.32, 0.10, 0.20, 0.05]

ocupacoes = ['Empregado c/ carteira', 'Empregado s/ carteira', 'Autônomo', 'Desempregado',
             'Estudante', 'Aposentado', 'Servidor público', 'Empresário']
p_ocup = [0.32, 0.09, 0.18, 0.10, 0.12, 0.08, 0.07, 0.04]

faixas_renda = ['Até 1 SM', '1–2 SM', '2–3 SM', '3–5 SM', '5–10 SM', 'Mais de 10 SM']
p_renda = [0.12, 0.20, 0.22, 0.23, 0.18, 0.05]

avaliacoes = ['Ótimo', 'Bom', 'Regular', 'Ruim', 'Péssimo']
p_avaliacao = [0.05, 0.25, 0.40, 0.20, 0.10]

fatores_preocupacao = ['crime e violência', 'pobreza e desigualdade', 'corrupção', 'educação',
                       'rede de transportes', 'desemprego', 'saúde', 'inflação', 'questões climáticas']
p_fatores = [0.29, 0.14, 0.11, 0.09, 0.08, 0.09, 0.10, 0.05, 0.05]

# ---------- Geração do banco ---------- #
dados = []

for mes in periodo:
    mes_ano_str = mes.strftime('%m/%Y')
    
    sexo = np.random.choice(sexos, size=amostra_mensal, p=p_sexos)
    idade = np.random.choice(faixas_etarias, size=amostra_mensal, p=p_idade)
    raca = np.random.choice(cores_raca, size=amostra_mensal, p=p_raca)
    esc = np.random.choice(escolaridades, size=amostra_mensal, p=p_esc)
    ocup = np.random.choice(ocupacoes, size=amostra_mensal, p=p_ocup)
    renda = np.random.choice(faixas_renda, size=amostra_mensal, p=p_renda)
    
    zona = np.random.choice(zonas, size=amostra_mensal, p=p_zonas)
    bairro = [random.choice(zona_para_bairros[z]) for z in zona]
    
    serv_saude = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_seg = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_cons = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_educ = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_amb = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_assist = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_transp = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    serv_saneam = np.random.choice(avaliacoes, size=amostra_mensal, p=p_avaliacao)
    
    fator = np.random.choice(fatores_preocupacao, size=amostra_mensal, p=p_fatores)
    
    for i in range(amostra_mensal):
        dados.append({
            'Mês/Ano': mes_ano_str,
            'Sexo': sexo[i],
            'Faixa etária': idade[i],
            'Cor/raça': raca[i],
            'Escolaridade': esc[i],
            'Ocupação': ocup[i],
            'Renda familiar (SM)': renda[i],
            'Bairro': bairro[i],
            'Zona': zona[i],
            'Saúde': serv_saude[i],
            'Segurança Pública': serv_seg[i],
            'Conservação Urbana e Patrimonial': serv_cons[i],
            'Educação': serv_educ[i],
            'Preservação ambiental': serv_amb[i],
            'Assistência Social': serv_assist[i],
            'Transportes': serv_transp[i],
            'Saneamento básico': serv_saneam[i],
            'Fator de maior preocupação': fator[i]
        })

df = pd.DataFrame(dados)

# -------- Salvar e mostrar -------- #
output_path = 'data/random_data.csv'
df.to_csv(output_path, index=False)

# Amostra
print(f'O arquivo final foi salvo em {output_path} e contém {df.shape[0]:,} linhas.')
