import json
import urllib.request
import urllib.error
import ssl

# Ignora verificação estrita de SSL caso o servidor da Câmara tenha certificado antigo
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

BASE_URL = "https://sapl.recife.pe.leg.br/api"

def buscar_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'FiscalizaRecife/1.0'})
    with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
        return json.loads(response.read().decode('utf-8'))

def classificar_tema(ementa):
    texto = ementa.lower()
    if any(p in texto for p in ['trânsito', 'ônibus', 'ciclovia', 'mobilidade', 'semáforo', 'transporte', 'cttu']):
        return "Mobilidade Urbana"
    if any(p in texto for p in ['árvore', 'ambiental', 'lixo', 'poda', 'reciclagem', 'parque', 'sustentável']):
        return "Meio Ambiente"
    if any(p in texto for p in ['asfalto', 'buraco', 'galeria', 'drenagem', 'emlurb', 'pavimentação', 'obra', 'iluminação']):
        return "Infraestrutura"
    if any(p in texto for p in ['escola', 'creche', 'professor', 'ensino', 'educação', 'aluno']):
        return "Educação"
    if any(p in texto for p in ['saúde', 'posto', 'upa', 'hospital', 'médico', 'vacina', 'remédio']):
        return "Saúde"
    if any(p in texto for p in ['segurança', 'guarda', 'policiamento', 'câmera', 'violência']):
        return "Segurança Pública"
    if any(p in texto for p in ['cultura', 'carnaval', 'patrimônio', 'turismo', 'esporte', 'lazer']):
        return "Cultura e Esporte"
    return "Administração e Outros"

def coletar_tudo():
    print("1. Mapeando vereadores e autores da Câmara do Recife...")
    autores_map = {}
    url_autores = f"{BASE_URL}/base/autor/?page_size=200"
    
    while url_autores:
        try:
            dados = buscar_json(url_autores)
            for autor in dados.get('results', []):
                autores_map[autor['id']] = autor.get('nome', 'Parlamentar')
            url_autores = dados.get('pagination', {}).get('links', {}).get('next')
        except Exception as e:
            print(f"Aviso ao buscar autores: {e}")
            break

    print(f"Total de autores mapeados: {len(autores_map)}")
    print("2. Coletando matérias legislativas (Projetos de Lei e Requerimentos)...")
    
    projetos_formatados = []
    # Coleta as matérias mais recentes (ajuste o limite de páginas conforme necessário)
    url_materias = f"{BASE_URL}/materia/materialegislativa/?ordering=-ano,-id&page_size=100"
    paginas_coletadas = 0
    max_paginas = 15  # Coleta até 1.500 matérias mais recentes para manter o site rápido

    while url_materias and paginas_coletadas < max_paginas:
        try:
            dados = buscar_json(url_materias)
            for m in dados.get('results', []):
                autores_ids = m.get('autores', [])
                nomes_autores = [autores_map.get(aid, "Mesa Diretora / Parlamentar") for aid in autores_ids]
                autor_str = ", ".join(nomes_autores) if nomes_autores else "Parlamentar"

                ementa = m.get('ementa', 'Sem ementa cadastrada.')
                tipo_sigla = m.get('__str__', '').split(' ')[0] if m.get('__str__') else 'MAT'
                numero = m.get('numero', '')
                ano = str(m.get('ano', ''))

                projetos_formatados.append({
                    "identificacao": m.get('__str__', f"{tipo_sigla} {numero}/{ano}"),
                    "numero": numero,
                    "autor": autor_str,
                    "ementa": ementa,
                    "ano": ano,
                    "tema": classificar_tema(ementa),
                    "status": "Em Tramitação" if m.get('em_tramitacao') else "Concluído / Arquivado"
                })

            paginas_coletadas += 1
            print(f"Página {paginas_coletadas} processada ({len(projetos_formatados)} matérias)...")
            url_materias = dados.get('pagination', {}).get('links', {}).get('next')
        except Exception as e:
            print(f"Erro na página {paginas_coletadas + 1}: {e}")
            break

    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(projetos_formatados, f, ensure_ascii=False, indent=2)

    print(f"Sucesso! {len(projetos_formatados)} registros salvos em dados.json.")

if __name__ == "__main__":
    coletar_tudo()