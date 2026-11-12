import requests
import json
import pandas as pd

API_URL = "https://e-processo.recife.pe.leg.br/consultas/materia/materias_legislativas_json"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ProjetoCivicTech-FiscalizaRecife/1.0",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "X-Requested-With": "XMLHttpRequest"
}

def classificar_tema(ementa: str) -> str:
    """Classifica automaticamente o tema com base na ementa."""
    if not ementa:
        return "Administração e Outros"
    
    texto = ementa.lower()
    regras = {
        "Mobilidade Urbana": ["trânsito", "ônibus", "ciclovia", "transporte", "pedestre", "estacionamento", "via pública", "mobilidade", "rua", "avenida"],
        "Saúde": ["saúde", "hospital", "ubs", "vacina", "medicamento", "atendimento médico", "caps", "autismo", "tea", "exame"],
        "Educação": ["escola", "ensino", "aluno", "professor", "creche", "educação", "merenda", "alfabetização", "estudante"],
        "Meio Ambiente": ["ambiental", "árvore", "lixo", "reciclagem", "rio capibaribe", "mangue", "sustentável", "poluição", "parque"],
        "Segurança Pública": ["guarda municipal", "segurança", "iluminação pública", "câmera", "monitoramento", "violência", "polícia"],
        "Direitos Humanos e Social": ["idoso", "mulher", "acessibilidade", "pcd", "vulnerabilidade", "moradia", "assistência social", "criança"],
        "Economia e Tributos": ["iptu", "iss", "isenção", "tributo", "comércio", "empreendedor", "taxa", "incentivo fiscal", "orçamento"],
        "Cultura e Turismo": ["cultura", "carnaval", "patrimônio", "turismo", "frevo", "arte", "evento cultural", "festival"]
    }
    
    for tema, palavras_chave in regras.items():
        if any(palavra in texto for palavra in palavras_chave):
            return tema
    return "Administração e Outros"

def coletar_historico():
    print("🔄 Iniciando coleta histórica da Câmara do Recife (Anos: 2025 e 2026)...")
    
    anos = ["2026", "2025"]
    todos_registros = []

    for ano in anos:
        print(f"📥 Coletando dados do ano de {ano}...")
        params = {
            "formato": "",
            "pagina": "1",
            "ordem_campo": "num_ident_basica",
            "ordem_direcao": "desc",
            "ano": ano
        }
        
        try:
            resposta = requests.get(API_URL, params=params, headers=HEADERS, timeout=15)
            if resposta.status_code == 200:
                dados = resposta.json()
                
                lista = []
                if isinstance(dados, list):
                    lista = dados
                elif isinstance(dados, dict):
                    for chave in ["results", "items", "data", "rows", "materias"]:
                        if chave in dados and isinstance(dados[chave], list):
                            lista = dados[chave]
                            break
                
                for item in lista:
                    sigla = item.get("sgl_tipo_materia", "PROJETO")
                    numero = item.get("num_ident_basica", "")
                    num_ano = item.get("ano_ident_basica", int(ano))
                    ementa = item.get("txt_ementa", "Sem ementa informada.")
                    autor = item.get("nom_autor", "Parlamentar / Mesa Diretora")
                    
                    identificacao = f"{sigla} {numero}/{num_ano}"
                    
                    todos_registros.append({
                        "identificacao": identificacao,
                        "numero": numero,
                        "ano": str(num_ano),
                        "autor": autor if autor else "Câmara Municipal",
                        "ementa": ementa,
                        "tema": classificar_tema(ementa),
                        "status": "Em Tramitação"
                    })
            else:
                print(f"❌ Erro HTTP para o ano {ano}: {resposta.status_code}")
        except Exception as e:
            print(f"❌ Erro na requisição do ano {ano}: {e}")

    # Salvando a base consolidada para o portal
    with open("projetos_recife_2026.json", "w", encoding="utf-8") as f:
        json.dump(todos_registros, f, ensure_ascii=False, indent=2)
        
    # Salvando também o CSV consolidado
    df = pd.DataFrame(todos_registros)
    df.to_csv("projetos_recife_historico_tratado.csv", index=False, encoding="utf-8-sig")

    print(f"\n✅ Coleta histórica concluída! Total de registros consolidados: {len(todos_registros)}")
    print("📁 Arquivos atualizados com sucesso.")

if __name__ == "__main__":
    coletar_historico()