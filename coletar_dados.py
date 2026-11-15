import json
import os

ARQUIVO_ORIGEM = "projetos_recife_2026.json"

def main():
    if not os.path.exists(ARQUIVO_ORIGEM):
        print(f"Erro: O arquivo '{ARQUIVO_ORIGEM}' não foi encontrado.")
        return

    with open(ARQUIVO_ORIGEM, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)

    # IMPRIME OS AUTORES QUE EXISTEM NO SEU ARQUIVO LOCAL PARA VERMOS
    autores_encontrados = set(item.get("autor", "").strip() for item in dados_brutos)
    print("Autores encontrados no seu JSON local:", autores_encontrados)

    # Se quiser forçar para ir tudo sem restrição de nome agora (para testar o site cheinho):
    dados_finais = dados_brutos

    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"Total de {len(dados_finais)} itens salvos no dados.json.")

if __name__ == "__main__":
    main()