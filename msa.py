import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import os
import calendar

# ------------------- Função para gerar datas de chamada -------------------
def gerar_datas(dia_aula, mes=None, ano=None):
    if mes is None:
        mes = datetime.today().month
    if ano is None:
        ano = datetime.today().year

    # Mapeamento de dias da semana
    dias_semana = {
        "Segunda e Quarta": [0, 2],  # 0=segunda, 2=quarta
        "Terça e Quinta": [1, 3]     # 1=terça, 3=quinta
    }

    dias_escolhidos = dias_semana[dia_aula]
    datas = []

    # Último dia do mês
    ultimo_dia = calendar.monthrange(ano, mes)[1]

    for d in range(1, ultimo_dia + 1):
        dia = date(ano, mes, d)
        if dia.weekday() in dias_escolhidos:
            datas.append(dia.strftime("%d/%m"))

    return datas


# ------------------- Função para criar planilha de chamada -------------------
def criar_planilha_chamada(turma, curso, dia_aula, horario, mes=None, ano=None):
    if mes is None:
        mes = datetime.today().month
    if ano is None:
        ano = datetime.today().year

    datas = gerar_datas(dia_aula, mes, ano)

    # Nome do arquivo
    arquivo_chamada = f"{turma}_chamada_{mes:02d}.csv"

    if os.path.exists(arquivo_chamada):
        df_chamada = pd.read_csv(arquivo_chamada)
    else:
        # Carregar alunos da turma
        df_turma = pd.read_csv(f"{turma}.csv")
        df_chamada = pd.DataFrame()
        df_chamada["Nome"] = df_turma["nome_beneficiario"]

        # Criar colunas de datas (aulas do mês)
        for data in datas:
            df_chamada[data] = ""

        df_chamada.to_csv(arquivo_chamada, index=False)

    return arquivo_chamada

# ------------------- Função para cadastro -------------------
def cadastrar_aluno(responsavel, whatsapp, cpf, endereco,
                    beneficiario, curso, dia_aula, horario, data_inicio):
    cols = ["gr","nome_responsavel","whatsapp","cpf","cidade_uf","endereco",
            "nome_beneficiario","curso","dia_aula","horario",
            "data_inicio","data_fim","status","faltas","turma"]

    df = pd.read_csv("df_alunos.csv") if os.path.exists("df_alunos.csv") else pd.DataFrame(columns=cols)

    gr = len(df) + 1
    turma_nome = f"{curso}_{dia_aula}_{horario}".replace(" ", "_")

    # Verifica quantos alunos já estão ativos na turma
    if os.path.exists(f"{turma_nome}.csv"):
        df_turma = pd.read_csv(f"{turma_nome}.csv")
        qtd_ativos = df_turma[df_turma["status"] == "Em andamento"].shape[0]
    else:
        df_turma = pd.DataFrame(columns=cols)
        qtd_ativos = 0

    # Define status conforme limite de vagas
    if qtd_ativos >= 20:
        status = "Em espera"
        data_inicio_fmt = ""
        data_fim_fmt = ""
    else:
        status = "Em andamento"
        data_fim = data_inicio + timedelta(weeks=8)
        data_inicio_fmt = data_inicio.strftime("%d/%m/%Y")
        data_fim_fmt = data_fim.strftime("%d/%m/%Y")

    novo = {
        "gr": gr,
        "nome_responsavel": responsavel.title(),
        "whatsapp": whatsapp,
        "cpf": cpf,
        "cidade_uf": "Guarujá/SP",
        "endereco": endereco.title(),
        "nome_beneficiario": beneficiario.title(),
        "curso": curso,
        "dia_aula": dia_aula,
        "horario": horario,
        "data_inicio": data_inicio_fmt,
        "data_fim": data_fim_fmt,
        "status": status,
        "faltas": 0,
        "turma": turma_nome
    }

    # Salva no arquivo geral
    df = pd.concat([df, pd.DataFrame([novo])], ignore_index=True)
    df.to_csv("df_alunos.csv", index=False)

    # Salva na planilha da turma
    df_turma = pd.concat([df_turma, pd.DataFrame([novo])], ignore_index=True)
    df_turma.to_csv(f"{turma_nome}.csv", index=False)

    if status == "Em espera":
        st.warning(f"Aluno {beneficiario.title()} cadastrado em **espera** para a turma {turma_nome} (limite de 20 alunos atingido).")
    else:
        st.success(f"Aluno {beneficiario.title()} cadastrado na turma {turma_nome} com sucesso!")

# ------------------- Função para pegar lista de turmas -------------------
def get_turmas():
    turmas = set()

    if os.path.exists("df_alunos.csv"):
        df = pd.read_csv("df_alunos.csv")
        turmas.update(df["turma"].dropna().unique().tolist())

    for file in os.listdir():
        # só considera CSVs que não são gerais e não são chamada
        if file.endswith(".csv") and file not in ["df_alunos.csv"] and "_chamada_" not in file:
            turmas.add(file.replace(".csv", ""))

    return sorted(list(turmas))


# ------------------- APP STREAMLIT -------------------
st.sidebar.title("Menu")
menu = st.sidebar.radio("Escolha uma opção", ["📌 Cadastrar Aluno", "📋 Ver Alunos", "📅 Chamada"])

# 📌 1. CADASTRO
if menu == "📌 Cadastrar Aluno":
    st.header("📌 Cadastro de Alunos")

    responsavel = st.text_input("Nome do responsável")
    whatsapp = st.text_input("WhatsApp (11 dígitos)")
    cpf = st.text_input("CPF (11 dígitos)")
    endereco = st.text_input("Endereço")
    beneficiario = st.text_input("Nome do beneficiário")

    curso = st.selectbox("Curso", ["Hardware","Inglês","Informática"])
    dia_aula = st.selectbox("Dia de aula", ["Segunda e Quarta","Terça e Quinta"])
    horario = st.selectbox("Horário", ["7h","13h","20h"])
    data_inicio = st.date_input("Data de início")

    if st.button("Cadastrar"):
        if not responsavel.replace(" ","").isalpha():
            st.error("Nome do responsável deve conter apenas letras.")
        elif not (whatsapp.isdigit() and len(whatsapp) == 11):
            st.error("WhatsApp deve conter 11 dígitos numéricos.")
        elif not (cpf.isdigit() and len(cpf) == 11):
            st.error("CPF deve conter 11 dígitos numéricos.")
        elif not beneficiario.replace(" ","").isalpha():
            st.error("Nome do beneficiário deve conter apenas letras.")
        else:
            cadastrar_aluno(responsavel, whatsapp, cpf, endereco,
                            beneficiario, curso, dia_aula, horario, data_inicio)

# 📋 2. LISTA DE ALUNOS
elif menu == "📋 Ver Alunos":
    st.header("📋 Lista de Alunos")

    turmas = get_turmas()
    escolha = st.selectbox("Selecione a turma", turmas)

    arquivo = f"{escolha}.csv"

    if os.path.exists(arquivo):
        df_view = pd.read_csv(arquivo)

        st.info(f"Editando alunos da turma: **{escolha}**")
        df_editado = st.data_editor(df_view, num_rows="dynamic", use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:
            if st.button("Salvar Alterações"):
                df_editado.to_csv(arquivo, index=False)

                # atualizar no df_alunos.csv também
                df_master = pd.read_csv("df_alunos.csv")
                df_master = df_master[df_master["turma"] != escolha]
                df_master = pd.concat([df_master, df_editado], ignore_index=True)
                df_master.to_csv("df_alunos.csv", index=False)

                st.success("Alterações salvas com sucesso!")

        with col2:
            if st.button("❌ Excluir Turma"):
                os.remove(arquivo)

                # Atualizar df_alunos removendo alunos dessa turma
                df_master = pd.read_csv("df_alunos.csv")
                df_master = df_master[df_master["turma"] != escolha]
                df_master.to_csv("df_alunos.csv", index=False)

                st.warning(f"Turma **{escolha}** excluída com sucesso!")
                st.rerun()
    else:
        st.warning("Nenhum dado encontrado para exibir.")


# 📅 3. CHAMADA
if menu == "📅 Chamada":
    st.header("📅 Registro de Chamada")

    # ---------- GERAR NOVA CHAMADA ----------
    st.subheader("➕ Gerar nova chamada")

    turmas = get_turmas()
    if not turmas:
        st.warning("Nenhuma turma encontrada para gerar chamada.")
    else:
        escolha_turma = st.selectbox("Selecione a turma", turmas, key="turma_chamada")
        mes = st.number_input("Digite o mês (1-12)", min_value=1, max_value=12, value=datetime.now().month)

        if st.button("Gerar chamada"):
            arquivo_turma = f"{escolha_turma}.csv"

            if os.path.exists(arquivo_turma):
                df_turma = pd.read_csv(arquivo_turma)

                # criar chamada com datas do mês (corretas pela turma)
                df_info = df_turma.iloc[0]  # pega info da turma
                dias = gerar_datas(df_info["dia_aula"], mes, datetime.now().year)

                # ------------------- SOMAR PRESENÇAS/FALTAS DOS MESES ANTERIORES ------------------- #
                chamadas_existentes = [
                    f for f in os.listdir()
                    if f.startswith(escolha_turma) and "_chamada_" in f and not f.endswith(f"_{mes:02d}.csv")
                ]

                faltas_acumuladas = {}
                presencas_acumuladas = {}

                for chamada in chamadas_existentes:
                    df_antigo = pd.read_csv(chamada, dtype=str)
                    df_antigo["Faltas"] = df_antigo["Faltas"].astype(int)
                    df_antigo["Presenças"] = df_antigo["Presenças"].astype(int)

                    for i, row in df_antigo.iterrows():
                        gr = row["gr"]
                        faltas_acumuladas[gr] = faltas_acumuladas.get(gr, 0) + row["Faltas"]
                        presencas_acumuladas[gr] = presencas_acumuladas.get(gr, 0) + row["Presenças"]

                # ------------------- CRIAR NOVA CHAMADA ------------------- #
                df_chamada = df_turma[["gr", "nome_beneficiario"]].copy()
                df_chamada.insert(2, "Faltas", 0)
                df_chamada.insert(3, "Presenças", 0)

                # aplica valores acumulados antes de criar colunas novas
                for i, row in df_chamada.iterrows():
                    gr = str(row["gr"])
                    df_chamada.at[i, "Faltas"] = faltas_acumuladas.get(gr, 0)
                    df_chamada.at[i, "Presenças"] = presencas_acumuladas.get(gr, 0)

                # garante que colunas de chamada sejam texto
                for dia in dias:
                    df_chamada[dia] = "N"
                    df_chamada[dia] = df_chamada[dia].astype(str)

                arquivo_chamada = f"{escolha_turma}_chamada_{mes:02d}.csv"
                df_chamada.to_csv(arquivo_chamada, index=False)
                st.success(f"Chamada criada: {arquivo_chamada} (com faltas/presenças acumuladas)")
            else:
                st.error("Turma não encontrada.")


    st.divider()

        # ---------- EDITAR CHAMADAS EXISTENTES ----------
    st.subheader("✏️ Editar chamadas existentes")

    chamadas = [f.replace(".csv", "") for f in os.listdir() if f.endswith(".csv") and "_chamada_" in f]

    if not chamadas:
        st.warning("Nenhuma chamada criada ainda.")
    else:
        escolha_chamada = st.selectbox("Selecione a planilha de chamada", chamadas)

        arquivo_chamada = f"{escolha_chamada}.csv"
        df_chamada = pd.read_csv(arquivo_chamada, dtype=str)  # força leitura como texto

        # converte faltas e presenças de volta para número
        df_chamada["Faltas"] = df_chamada["Faltas"].astype(int)
        df_chamada["Presenças"] = df_chamada["Presenças"].astype(int)

        st.info(f"Editando chamada: **{arquivo_chamada}**")
        df_editado = st.data_editor(df_chamada, num_rows="dynamic", use_container_width=True)

        col1, col2 = st.columns(2)

        with col1:    
            if st.button("Salvar Chamada"):
                # Recalcula faltas/presenças antes de salvar
                for i, row in df_editado.iterrows():
                    respostas = row.drop(labels=["gr", "nome_beneficiario", "Faltas", "Presenças"])
                    faltas = (respostas == "A").sum()
                    presencas = (respostas == "P").sum()
                    df_editado.at[i, "Faltas"] = faltas
                    df_editado.at[i, "Presenças"] = presencas

                df_editado.to_csv(arquivo_chamada, index=False)

                # Atualizar faltas no cadastro da turma
                turma_nome = escolha_chamada.split("_chamada_")[0]
                if os.path.exists(f"{turma_nome}.csv"):
                    df_turma = pd.read_csv(f"{turma_nome}.csv")
                    for i, row in df_editado.iterrows():
                        df_turma.loc[df_turma["gr"] == row["gr"], "faltas"] = row["Faltas"]
                    df_turma.to_csv(f"{turma_nome}.csv", index=False)

                # ------------------ NOVA LÓGICA ------------------ #
                arquivo_reprovado = f"{escolha_chamada}_reprovado.csv"
                arquivo_finalizado = f"{escolha_chamada}_finalizado.csv"

                df_reprovados = pd.read_csv(arquivo_reprovado) if os.path.exists(arquivo_reprovado) else pd.DataFrame(columns=df_editado.columns)
                df_finalizados = pd.read_csv(arquivo_finalizado) if os.path.exists(arquivo_finalizado) else pd.DataFrame(columns=df_editado.columns)

                mover_reprovados = []
                mover_finalizados = []

                for _, row in df_editado.iterrows():
                    faltas = int(row["Faltas"])
                    presencas = int(row["Presenças"])
                    gr = row["gr"]

                    # Verifica se já está nos arquivos antes de mover
                    ja_reprovado = gr in df_reprovados["gr"].values
                    ja_finalizado = gr in df_finalizados["gr"].values

                    # ✅ Regra de reprovação
                    if faltas > 3 and not ja_reprovado:
                        mover_reprovados.append(row)

                    # ✅ Regra de finalização
                    elif (presencas >= 16 or (presencas + faltas) >= 16 and faltas <= 2) and not ja_finalizado:
                        mover_finalizados.append(row)

                # Atualiza planilhas
                if mover_reprovados:
                    df_reprovados = pd.concat([df_reprovados, pd.DataFrame(mover_reprovados)], ignore_index=True)
                    df_reprovados.to_csv(arquivo_reprovado, index=False)

                if mover_finalizados:
                    df_finalizados = pd.concat([df_finalizados, pd.DataFrame(mover_finalizados)], ignore_index=True)
                    df_finalizados.to_csv(arquivo_finalizado, index=False)

                # Remove da chamada os que foram movidos
                df_editado = df_editado[
                    ~df_editado["gr"].isin(df_reprovados["gr"]) &
                    ~df_editado["gr"].isin(df_finalizados["gr"])
                ]
                df_editado.to_csv(arquivo_chamada, index=False)

                st.success("✅ Chamada salva | Atualizado cadastro | Movidos para Reprovados/Finalizados")

            
        with col2:
            if st.button("❌ Excluir Chamada"):
                os.remove(arquivo_chamada)
                st.warning(f"Chamada **{escolha_chamada}** excluída com sucesso!")
                st.rerun()
        
                # ------------------ VISUALIZAÇÃO ------------------ #
        st.subheader("📌 Alunos Reprovados")
        if not df_reprovados.empty:
            df_reprovados_edit = st.data_editor(df_reprovados, num_rows="dynamic", use_container_width=True)
            df_reprovados_edit.to_csv(arquivo_reprovado, index=False)
        else:
            st.info("Nenhum aluno reprovado até agora.")

        st.subheader("📌 Alunos Finalizados")
        if not df_finalizados.empty:
            df_finalizados_edit = st.data_editor(df_finalizados, num_rows="dynamic", use_container_width=True)
            df_finalizados_edit.to_csv(arquivo_finalizado, index=False)
        else:
            st.info("Nenhum aluno finalizado até agora.")


