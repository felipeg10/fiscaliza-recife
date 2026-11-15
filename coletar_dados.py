from curl_cffi import requests
import json
import time

BASE_URL = "https://sapl.recife.pe.leg.br/api"
ANO_ALVO = 2026

# Cria uma sessão que imita a assinatura TLS e cabeçalhos de um Chrome real
sessao = requests.Session(impersonate="chrome124")

HEADERS = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://sapl.recife.pe.leg.br/materia/pesquisar-materia",
    "Origin": "https://sapl.recife.pe.leg.br",
    "Connection": "keep-alive"
}

def aquecer_sessao():
    """Acessa a página inicial primeiro para pegar cookies legítimos do firewall/WAF."""
    try:
        print("0. Inicializando sessão e obtendo cookies do SAPL...")
        sessao.get("https://sapl.recife.pe.leg.br/materia/pesquisar-materia", headers=HEADERS, timeout=20)
        time.sleep(1.5)
    except Exception as e:
        print(f"Aviso ao aquecer sessão: {e}")

def buscar_todos_os_itens(endpoint, params=None):
    """Percorre as páginas com retentativas e sem sobrecarregar o servidor."""
    resultados = []
    url = f"{BASE_URL}/{endpoint}/"
    pagina = 1
    
    while url:
        sucesso = False
        for tentativa in range(3):
            try:
                resp = sessao.get(url, headers=HEADERS, params=params, timeout=25)
                if resp.status_code == 503:
                    print(f"Servidor engasgou (503) na página {pagina}. Aguardando 5s para tentar de novo...")
                    time.sleep(5)
                    continue
                
                resp.raise_for_status()
                dados = resp.json()
                
                itens_pagina = dados.get("results", [])
                resultados.extend(itens_pagina)
                print(f"   -> Página {pagina} coletada ({len(itens_pagina)} itens). Total parcial: {len(resultados)}")
                
                url = dados.get("pagination", {}).get("links", {}).get("next")
                params = None
                pagina += 1
                sucesso = True
                time.sleep(1.2)  # Pausa humana entre páginas
                break
            except Exception as e:
                print(f"Erro na tentativa {tentativa+1} em {url}: {e}")
                time.sleep(3)
        
        if not sucesso:
            print("Falha persistente após 3 tentativas. Encerrando paginação deste endpoint.")
            break
            
    return resultados

def classificar_tema(ementa):
    texto = ementa.lower()
    if any(p in texto for p in ["saúde", "hospital", "ubs", "médic", "vacina", "psicológ", "caps"]):
        return "Saúde"
    if any(p in texto for p in ["escola", "educação", "ensino", "professor", "creche", "aluno"]):
        return "Educação"
    if any(p in texto for p in ["ônibus", "trânsito", "ciclofaixa", "semáforo", "calçada", "mobilidade", "transporte"]):
        return "Mobilidade Urbana"
    if any(p in texto for p in ["asfalto", "drenagem", "canal", "encosta", "barreira", "buraco", "iluminação", "obra"]):
        return "Infraestrutura"
    if any(p in texto for p in ["segurança", "guarda municipal", "policiamento", "violência", "câmera"]):
        return "Segurança Pública"
    if any(p in texto for p in ["árvore", "verde", "parque", "lixo", "reciclagem", "ambiental", "animal", "sustent"]):
        return "Meio Ambiente"
    return "Administração e Outros"

def main():
    aquecer_sessao()

    print("1. Mapeando tipos de matéria legislativa...")
    tipos_raw = buscar_todos_os_itens("materia/tipomaterialegislativo")
    mapa_tipos = {t["id"]: {"sigla": t["sigla"], "descricao": t["descricao"]} for t in tipos_raw}

    print("2. Mapeando parlamentares...")
    autores_raw = buscar_todos_os_itens("base/autor")
    mapa_autores = {}
    for a in autores_raw:
        if a.get("tipo") == 1 or "Parlamentar" in str(a.get("__str__", "")):
            mapa_autores[a["id"]] = a.get("nome", "").strip()

    print(f"3. Coletando proposições de {ANO_ALVO} (sem forçar page_size alto)...")
    # Omitimos page_size=100 para usar o padrão leve do servidor (geralmente 10 ou 20 por página)
    materias_raw = buscar_todos_os_itens("materia/materiaparlamentar", params={"ano": ANO_ALVO})
    print(f"Total bruto coletado em {ANO_ALVO}: {len(materias_raw)}")

    if not materias_raw:
        print("Nenhuma matéria retornada. O endpoint /api/ pode estar bloqueado no servidor.")
        return

    dados_finais = []
    for m in materias_raw:
        autores_ids = m.get("autores", [])
        if not autores_ids:
            continue

        nome_autor = None
        for aid in autores_ids:
            if aid in mapa_autores:
                nome_autor = mapa_autores[aid]
                break
        
        if not nome_autor:
            continue

        tipo_info = mapa_tipos.get(m.get("tipo"), {"sigla": "MAT", "descricao": "Matéria Legislativa"})
        numero = m.get("numero", "")
        ano = str(m.get("ano", ANO_ALVO))
        ementa = m.get("ementa", "Sem ementa cadastrada.").strip()
        id_sapl = m.get("id")
        
        texto_original = m.get("texto_original")
        url_oficial = f"https://sapl.recife.pe.leg.br/materia/{id_sapl}"
        url_pdf = texto_original if texto_original else url_oficial

        status = "Em Tramitação"
        if m.get("em_tramitacao") is False:
            status = "Tramitada / Arquivada"

        dados_finais.append({
            "id_sapl": id_sapl,
            "identificacao": f"{tipo_info['sigla']} {numero}/{ano}",
            "tipo_materia": tipo_info["descricao"],
            "numero": numero,
            "autor": nome_autor,
            "ementa": ementa,
            "ano": ano,
            "tema": classificar_tema(ementa),
            "status": status,
            "url_oficial": url_oficial,
            "url_pdf": url_pdf
        })

    dados_finais.sort(key=lambda x: x["id_sapl"], reverse=True)

    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"Sucesso! {len(dados_finais)} proposições reais salvas em dados.json.")

if __name__ == "__main__":
    main()