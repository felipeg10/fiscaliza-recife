import json
import os

ARQUIVO_ORIGEM = "projetos_recife_2026.json"

def main():
    if not os.path.exists(ARQUIVO_ORIGEM):
        print(f"Erro: O arquivo '{ARQUIVO_ORIGEM}' não foi encontrado na pasta do projeto.")
        return

    print(f"Lendo dados de '{ARQUIVO_ORIGEM}'...")
    with open(ARQUIVO_ORIGEM, "r", encoding="utf-8") as f:
        dados_brutos = json.load(f)

    # Lista oficial e rigorosa dos 15 parlamentares vigentes
    vereadores_ativos = [
        "Cida Pedrosa", "Liana Cirne", "Dani Portela", "Samuel Salazar", 
        "Romerinho Jatobá", "Felipe Alecrim", "Alcides Teixeira Neto", 
        "Aderaldo Pinto", "Almir Fernando", "Eriberto Rafael", 
        "Hélio Guabiraba", "Ivan Moraes", "Michelle Collins", 
        "Osmar Ricardo", "Rinaldo Junior"
    ]

    dados_finais = []
    for item in dados_brutos:
        autor = item.get("autor", "").strip()
        # Filtra apenas quem pertence à legislatura atual
        if autor in vereadores_ativos:
            dados_finais.append(item)

    # Ordena do ID mais recente para o mais antigo (ou mantém a ordem original)
    dados_finais.sort(key=lambda x: x.get("id_sapl", 0), reverse=True)

    # Salva no arquivo oficial que o site lê
    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados_finais, f, ensure_ascii=False, indent=4)

    print(f"Sucesso absoluto! {len(dados_finais)} proposições válidas dos 15 vereadores salvas em dados.json.")
    print("O ranking e os filtros do site agora estão perfeitamente sincronizados.")

if __name__ == "__main__":
    main()