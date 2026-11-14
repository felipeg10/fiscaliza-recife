import json
import os
import requests

BASE_URL = "https://sapl.recife.pe.leg.br"
API_MATERIAS = f"{BASE_URL}/api/materia/materialegislativa/"
ARQUIVO_SAIDA = "dados.json"
ANO_ALVO = "2026"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*;q=0.8",
}

def classificar_tema(ementa):
    texto = ementa.lower()
    if any(p in texto for p in ["saúde", "hospital", "upa", "médic", "vacina", "enferm"]):
        return "Saúde"
    if any(p in texto for p in ["escola", "creche", "educação", "ensino", "professor"]):
        return "Educação"
    if any(p in texto for p in ["ônibus", "trânsito", "ciclovia", "rua", "mobilidade"]):
        return "Mobilidade Urbana"
    if any(p in texto for p in ["drenagem", "encosta", "barreira", "pavimentação", "obra"]):
        return "Infraestrutura"
    if any(p in texto for p in ["meio ambiente", "lixo", "reciclagem", "parque", "árvore"]):
        return "Meio Ambiente"
    if any(p in texto for p in ["segurança", "guarda municipal", "violência", "polícia"]):
        return "Segurança Pública"
    return "Administração e Outros"

def atualizar_base():
    print("🔎 Conectando ao SAPL da Câmara do Recife para sincronização...")
    registros = []
    
    try:
        # Busca paginada ou lote ampliado da API oficial
        response = requests.get(f"{API_MATERIAS}?ano={ANO_ALVO}&page_size=200", headers=HEADERS, timeout=30)
        
        if response.status_code == 200:
            dados = response.json()
            resultados = dados.get("results", [])
            
            for item in resultados:
                mat_id = item.get("id")
                autores = item.get("autores_nomes", "Autoria não informada")
                autor_str = ", ".join(autores) if isinstance(autores, list) else str(autores)
                ementa = (item.get("ementa") or "").strip()
                
                registros.append({
                    "id_sapl": mat_id,
                    "identificacao": item.get("__str__", f"Matéria {mat_id}"),
                    "tipo_materia": item.get("tipo_descricao") or "Matéria Legislativa",
                    "autor": autor_str,
                    "ementa": ementa,
                    "ano": ANO_ALVO,
                    "tema": classificar_tema(ementa),
                    "status": "Em Tramitação" if item.get("em_tramitacao", True) else "Concluída",
                    "url_oficial": f"{BASE_URL}/materia/{mat_id}" if mat_id else f"{BASE_URL}/materia/pesquisar-materia",
                    "url_pdf": f"{BASE_URL}{item.get('texto_original')}" if item.get('texto_original') else f"{BASE_URL}/materia/{mat_id}"
                })
        else:
            print(f"⚠️ Servidor retornou status {response.status_code}")
            
    except Exception as e:
        print(f"⚠️ Erro ao acessar a API (instabilidade temporária): {e}")

    # Se conseguiu novos dados, atualiza o JSON. Se o servidor da Câmara caiu (503), 
    # o script preserva o arquivo existente para não deixar o site vazio.
    if registros:
        with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as f:
            json.dump(registros, f, ensure_ascii=False, indent=2)
        print(f"🎉 Sincronização concluída! {len(registros)} registros salvos em '{ARQUIVO_SAIDA}'.")
    else:
        print("⚠️ Nenhum registro novo obtido devido a instabilidade. Base local preservada.")

if __name__ == "__main__":
    atualizar_base()