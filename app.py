import streamlit as st
import pandas as pd
import plotly.express as px
import database

# 1. Inicializa o banco de dados (se não existir, ele é criado)
database.init_db()

st.set_page_config(page_title="Jornada de Compra", page_icon="📈", layout="wide")

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("Menu de Clientes")

# Carrega os clientes direto do banco SQLite
df_clientes = database.listar_clientes()
opcoes_clientes = ["➕ Cadastrar Novo Cliente"]

if not df_clientes.empty:
    lista_nomes = df_clientes['nome'].tolist()
    # Junta a opção de cadastrar com os nomes dos clientes
    opcoes_clientes.extend(lista_nomes)

cliente_selecionado = st.sidebar.selectbox("Dashboard Atual:", opcoes_clientes)

# --- FUNÇÕES AUXILIARES ---
def format_rs(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# ==========================================
# TELA 1: CADASTRO DE NOVO CLIENTE
# ==========================================
if cliente_selecionado == "➕ Cadastrar Novo Cliente":
    st.title("📝 Cadastro de Conta/Cliente")
    st.markdown(
        "Preencha as informações financeiras e das etapas do funil abaixo "
        "para gerar um dashboard exclusivo para essa empresa/campanha."
    )
    
    with st.form("cadastro_form", clear_on_submit=False):
        st.subheader("1. Informações Básicas e Financeiras")
        nome = st.text_input("Nome do Cliente ou Empresa")
        
        col_f1, col_f2 = st.columns(2)
        inv_trafego = col_f1.number_input("Investimento em Tráfego (R$)", min_value=0.0, step=100.0)
        inv_agencia = col_f2.number_input("Investimento com Agência (R$)", min_value=0.0, step=100.0)
        
        col_f3, col_f4 = st.columns(2)
        vendas = col_f3.number_input("Valor em Vendas Brutas / Receita (R$)", min_value=0.0, step=100.0)
        custos = col_f4.number_input("Custos Variáveis da Empresa/Produto (R$)", min_value=0.0, step=100.0)
        
        submit = st.form_submit_button("Salvar Cliente e Gerar Dashboard", type="primary")
        
        if submit:
            if nome.strip() == "":
                st.error("Por favor, preencha o nome do cliente antes de salvar!")
            else:
                # Inicializa valores do funil com zero (serão preenchidos automaticamente depois)
                funil_valores = (0, 0, 0, 0, 0, 0, 0, 0)
                database.inserir_cliente(nome, inv_trafego, inv_agencia, vendas, custos, funil_valores)
                st.success(
                    f"Cliente '{nome}' cadastrado com sucesso! Selecione ele na "
                    "barra lateral à esquerda para ver os gráficos."
                )


# ==========================================
# TELA 2: DASHBOARD DO CLIENTE ESCOLHIDO
# ==========================================
else:
    # Busca o ID usando o nome que o usuário clicou
    cliente_id = df_clientes[df_clientes['nome'] == cliente_selecionado].iloc[0]['id']
    dados = database.obter_dados_cliente(cliente_id)
    
    st.title(f"🎯 Dashboard: {dados['nome']}")
    st.markdown("Acompanhamento financeiro em tempo real e análise detalhada do funil de conversão.")
    st.divider()

    st.header("📊 Resumo Financeiro")
    
    # Resgatando do Banco
    investimento_trafego = float(dados['inv_trafego'])
    investimento_agencia = float(dados['inv_agencia'])
    investimento_total_marketing = investimento_trafego + investimento_agencia
    valor_vendas = float(dados['vendas'])
    custos_variaveis = float(dados['custos'])

    # Evita erros de divisão por zero caso o usuário coloque "R$ 0" lá no formulário
    roas = (valor_vendas / investimento_trafego) if investimento_trafego > 0 else 0.0
    margem_contribuicao = valor_vendas - custos_variaveis
    roi = (
        ((margem_contribuicao - investimento_total_marketing) / investimento_total_marketing) * 100
    ) if investimento_total_marketing > 0 else 0.0
    margem_percentual = (margem_contribuicao / valor_vendas * 100) if valor_vendas > 0 else 0.0

    # Render dos Cartões (Aquele código seguro de 2 linhas x 3 colunas)
    col1, col2, col3 = st.columns(3)
    col1.metric("Inv. Tráfego", format_rs(investimento_trafego))
    col2.metric("Inv. Agência", format_rs(investimento_agencia))
    col3.metric("Inv. Marketing", format_rs(investimento_total_marketing))

    st.write("") 

    col4, col5, col6 = st.columns(3)
    col4.metric("Vendas (Receita)", format_rs(valor_vendas))
    col5.metric("ROAS", f"{roas:.2f}x")
    col6.metric("ROI", f"{roi:.1f}%")

    st.info(
        f"**Margem de Contribuição:** {format_rs(margem_contribuicao)} "
        f"({margem_percentual:.1f}%) da Receita Bruta"
    )

    st.divider()

    st.header("🌪️ Funil de Conversão")

    # Montando as Etapas padronizadas com os Números Específicos do DB
    etapas = [
        "Alcance", "Interação", "Contatos", "Conversão", 
        "Encantamento", "Expansão", "Defesa", "Indicação"
    ]
    valores = [
        int(dados['alcance']), int(dados['interacao']), int(dados['contatos']), int(dados['conversao']),
        int(dados['encantamento']), int(dados['expansao']), int(dados['defesa']), int(dados['indicacao'])
    ]

    df = pd.DataFrame(dict(Volume=valores, Etapa=etapas))
    df['Tamanho Visual'] = list(range(len(df), 0, -1)) # Evita achatamento do funil

    # Lógica que lida perfeitamente se alguma etapa ficar O zero (shift zero gera infinidade)
    df['Tx Conv Etapa Anterior'] = (df['Volume'] / df['Volume'].replace(0, 1).shift(1)) * 100
    df['Taxa Formatada'] = df['Tx Conv Etapa Anterior'].apply(
        lambda x: f"{x:.1f}%" if pd.notnull(x) else "- (Início da Jornada)"
    )

    col_funil, col_tabela = st.columns([2, 1])

    with col_funil:
        fig = px.funnel(
            df, 
            x='Tamanho Visual', 
            y='Etapa', 
            title="Progresso da Audiência",
            color_discrete_sequence=['#4A90E2'],
            custom_data=['Volume', 'Taxa Formatada'] 
        )
        fig.update_traces(
            text=df['Volume'].apply(lambda x: f"{x:,}".replace(",", ".")),
            textinfo="text",
            hovertemplate=(
                "<b>%{y}</b><br>Volume Real: %{customdata[0]}"
                "<br>Conversão: %{customdata[1]}<extra></extra>"
            )
        )
        st.plotly_chart(fig, use_container_width=True, theme="streamlit")

    with col_tabela:
        st.markdown("##### Tabela de Performance")

        # Encontra o valor mínimo em 'Tx Conv Etapa Anterior' (ignorando o primeiro NaN)
        min_conv = df['Tx Conv Etapa Anterior'].min()

        def highlight_min_row(row):
            is_min = row['Tx Conv Etapa Anterior'] == min_conv and pd.notnull(min_conv)
            return ['background-color: #ffcccc' if is_min else '' for _ in row]

        # Prepara o DF para exibição (escondendo a coluna de cálculo no final)
        df_display = df[['Etapa', 'Volume', 'Taxa Formatada', 'Tx Conv Etapa Anterior']].rename(
            columns={'Taxa Formatada': 'Tx Conversão'}
        )

        st.dataframe(
            df_display.style.apply(highlight_min_row, axis=1),
            column_config={
                "Tx Conv Etapa Anterior": None,  # Esconde a coluna usada no cálculo
            },
            hide_index=True,
            use_container_width=True
        )
