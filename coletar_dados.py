import urllib.request
import json
import time
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'pt-BR,pt;q=0.9',
    'Referer': 'https://sapl.recife.pe.leg.br/'
}

ARQUIVO_SAIDA = 'dados.json'

def fazer_requisicao(url, tentativas=4):
    for tentativa in range(1, tentativas + 1):
        try:
            req = urllib.request.Request(url, headers=HEADERS)
            with urllib.request.urlopen(req, timeout=25) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception as e:
            print(f"Tentativa {tentativa} falhou para {url}: {e}")
            time.sleep(tentativa * 3)
    return None

def carregar_historico_local():
    if os.path.exists(ARQUIVO_SAIDA):
        try:
            with open(ARQUIVO_SAIDA, 'r', encoding='utf-8') as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    return dados
        except Exception as e:
            print(f"Aviso ao ler histórico local: {e}")
    return []

def classificar_tema(ementa):
    texto = ementa.lower()
    if any(p in texto for p in ['saúde', 'hospital', 'upa', 'médico', 'vacina', 'medicamento', 'clínica', 'policlínica', 'caps']):
        return 'Saúde'
    if any(p in texto for p in ['escola', 'educação', 'creche', 'professor', 'aluno', 'ensino', 'merenda', 'alfabetização']):
        return 'Educação'
    if any(p in texto for p in ['trânsito', 'ônibus', 'ciclofaixa', 'ciclovia', 'semáforo', 'cttu', 'transporte', 'mobilidade', 'asfalto', 'recapeamento']):
        return 'Mobilidade Urbana'
    if any(p in texto for p in ['drenagem', 'canal', 'galeria', 'emlurb', 'buraco', 'iluminação', 'encosta', 'barreira', 'pavimentação', 'obra']):
        return 'Infraestrutura'
    if any(p in texto for p in ['segurança', 'guarda municipal', 'videomonitoramento', 'policiamento', 'violência', 'ronda']):
        return 'Segurança Pública'
    if any(p in texto for p in ['meio ambiente', 'árvore', 'arborização', 'capibaribe', 'mangue', 'lixo', 'reciclagem', 'animal', 'veterinário', 'sustentável']):
        return 'Meio Ambiente'
    if any(p in texto for p in ['cultura', 'esporte', 'carnaval', 'biblioteca', 'quadra', 'lazer', 'artista', 'teatro', 'música']):
        return 'Cultura e Esporte'
    return 'Administração e Outros'

def mapear_tabela(endpoint, campo_nome='nome'):
    mapa = {}
    url = f"https://sapl.recife.pe.leg.br/api/{endpoint}/?page_size=50"
    while url:
        dados = fazer_requisicao(url)
        if not dados or 'results' not in dados:
            break
        for item in dados['results']:
            mapa[item['id']] = item.get(campo_nome) or item.get('descricao') or str(item['id'])
        url = dados.get('next')
        time.sleep(1.2)
    return mapa

def coletar():
    historico = carregar_historico_local()
    print(f"1. Histórico local carregado: {len(historico)} matérias existentes.")

    banco_materias = {item['identificacao']: item for item in historico if 'identificacao' in item}

    print("2. Mapeando tipos de matéria e autores da Câmara...")
    mapa_tipos = mapear_tabela("materia/tipomaterialegislativa", "descricao")
    mapa_autores = mapear_tabela("base/autor", "nome")

    if not mapa_tipos:
        print("⚠️ API do SAPL indisponível no momento (Erro 503). Mantendo histórico local intacto.")
        return

    print("3. Buscando matérias legislativas recentes...")
    url_materias = "https://sapl.recife.pe.leg.br/api/materia/materialegislativa/?page_size=50&o=-id"
    paginas_coletadas = 0
    max_paginas = 20  # Coleta até 1.000 matérias por execução em lotes leves
    novos_adicionados = 0

    while url_materias and paginas_coletadas < max_paginas:
        dados = fazer_requisicao(url_materias)
        if not dados or 'results' not in dados:
            print("⚠️ Interrupção na coleta por instabilidade do servidor. Salvando o progresso atual...")
            break

        for m in dados['results']:
            tipo_id = m.get('tipo')
            tipo_nome = mapa_tipos.get(tipo_id, 'Matéria Legislativa')
            
            str_repr = m.get('__str__', '')
            sigla = str_repr.split(' ')[0] if str_repr else 'MAT'
            numero = m.get('numero', '')
            ano = str(m.get('ano', ''))
            
            identificacao = f"{sigla} {numero}/{ano}"
            ementa = m.get('ementa', 'Sem ementa informada.')
            
            autor_nome = "Não informado"
            autores_vinculados = m.get('autores', [])
            if autores_vinculados and isinstance(autores_vinculados, list):
                primeiro_autor_id = autores_vinculados[0].get('autor')
                if primeiro_autor_id in mapa_autores:
                    autor_nome = mapa_autores[primeiro_autor_id]

            tema = classificar_tema(ementa)
            status = "Em Tramitação"

            item_novo = {
                "identificacao": identificacao,
                "tipo_materia": tipo_nome,
                "numero": numero,
                "autor": autor_nome,
                "ementa": ementa,
                "ano": ano,
                "tema": tema,
                "status": status
            }

            if identificacao not in banco_materias:
                novos_adicionados += 1
            
            banco_materias[identificacao] = item_novo

        url_materias = dados.get('next')
        paginas_coletadas += 1
        time.sleep(1.5)

    lista_final = list(banco_materias.values())
    
    with open(ARQUIVO_SAIDA, 'w', encoding='utf-8') as f:
        json.dump(lista_final, f, ensure_ascii=False, indent=4)

    print(f"✅ Concluído! Total de matérias no arquivo consolidado: {len(lista_final)} ({novos_adicionados} novas adicionadas).")

if __name__ == '__main__':
    coletar()