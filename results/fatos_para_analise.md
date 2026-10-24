### 6.1. Como o aumento de usuários afeta o tempo de resposta?

- **Perfil 1 (Leitura)**:
  - Tempo Médio: A (30 u): 15.0 ms, B (80 u): 41.1 ms, C (150 u): 139.9 ms (aumento de 9.31x de A para C)
  - Percentil 95 (P95): A: 27.9 ms, B: 98.2 ms, C: 440.2 ms
- **Perfil 2 (Escrita)**:
  - Tempo Médio: A (30 u): 21.0 ms, B (80 u): 55.3 ms, C (150 u): 193.1 ms (aumento de 9.21x de A para C)
  - Percentil 95 (P95): A: 39.6 ms, B: 132.2 ms, C: 607.7 ms

*Interpretação:* O aumento da concorrência provoca a formação de filas no API Gateway e nos microsserviços, elevando o tempo de espera de processamento e entrada/saída. A latência média cresce progressivamente, e a métrica P95 revela a degradação da cauda de distribuição com picos de latência sob carga elevada (150 usuários).

### 6.2. Qual perfil apresenta maior vazão?

- Cenário A (30 u) / Perfil 2 (Escrita): **17.87 req/s** (6434 requisições na janela medida)
- Cenário A (30 u) / Perfil 1 (Leitura): **19.00 req/s** (6838 requisições na janela medida)
- Cenário B (80 u) / Perfil 2 (Escrita): **43.65 req/s** (15714 requisições na janela medida)
- Cenário B (80 u) / Perfil 1 (Leitura): **49.41 req/s** (17786 requisições na janela medida)
- Cenário C (150 u) / Perfil 2 (Escrita): **65.15 req/s** (23453 requisições na janela medida)
- Cenário C (150 u) / Perfil 1 (Leitura): **74.73 req/s** (26903 requisições na janela medida)

*Interpretação:* O **Perfil 1 (Leitura)** apresentou a maior vazão média (47.71 req/s contra 42.22 req/s, diferença de 5.49 req/s). Isso ocorre porque requisições de leitura não realizam inserções no banco, validações de payload ou bloqueios transacionais, permitindo que o customers-service e o vets-service processem as respostas de forma mais rápida.

### 6.3. Quais operações apresentam maior degradação?

- **Perfil 1 (Leitura)** (Fator de aumento do Tempo Médio C / A):
  - `GET /owners`: **10.13x** (de 18.1 ms no cenário A para 183.2 ms no cenário C)
  - `POST /owners`: **10.01x** (de 23.9 ms no cenário A para 239.0 ms no cenário C)
  - `GET /vets`: **8.01x** (de 12.3 ms no cenário A para 98.4 ms no cenário C)
  - `GET /owners/{id}`: **7.99x** (de 11.0 ms no cenário A para 87.9 ms no cenário C)
- **Perfil 2 (Escrita)** (Fator de aumento do Tempo Médio C / A):
  - `POST /owners`: **9.70x** (de 28.6 ms no cenário A para 277.7 ms no cenário C)
  - `GET /owners`: **9.68x** (de 21.2 ms no cenário A para 205.1 ms no cenário C)
  - `GET /vets`: **7.80x** (de 13.5 ms no cenário A para 104.9 ms no cenário C)
  - `GET /owners/{id}`: **7.74x** (de 12.9 ms no cenário A para 100.1 ms no cenário C)

*Interpretação:* A operação `GET /owners` sofre forte impacto porque busca a lista inteira de proprietários no banco e transfere uma carga útil maior de dados. Já `GET /owners/{id}` realiza busca indexada pontual por ID, mantendo latência proporcionalmente menor. As operações de escrita (`POST /owners`) também sofrem contenção transacional.

### 6.4. Como o consumo de CPU varia entre os cenários?

- **Perfil 1 (Leitura)**:
  - api-gateway (Cenário A - 30 u): média de **23.7%**, pico de 25.6%
  - api-gateway (Cenário B - 80 u): média de **58.0%**, pico de 62.4%
  - api-gateway (Cenário C - 150 u): média de **87.3%**, pico de 93.9%
  - customers-service (Cenário A - 30 u): média de **30.7%**, pico de 33.1%
  - customers-service (Cenário B - 80 u): média de **68.8%**, pico de 74.2%
  - customers-service (Cenário C - 150 u): média de **95.2%**, pico de 102.6%
  - vets-service (Cenário A - 30 u): média de **11.9%**, pico de 12.8%
  - vets-service (Cenário B - 80 u): média de **23.9%**, pico de 25.8%
  - vets-service (Cenário C - 150 u): média de **35.5%**, pico de 38.2%
  - visits-service (Cenário A - 30 u): média de **6.4%**, pico de 6.9%
  - visits-service (Cenário B - 80 u): média de **10.5%**, pico de 11.3%
  - visits-service (Cenário C - 150 u): média de **14.2%**, pico de 15.3%
- **Perfil 2 (Escrita)**:
  - api-gateway (Cenário A - 30 u): média de **24.0%**, pico de 26.0%
  - api-gateway (Cenário B - 80 u): média de **57.7%**, pico de 61.9%
  - api-gateway (Cenário C - 150 u): média de **85.7%**, pico de 92.6%
  - customers-service (Cenário A - 30 u): média de **34.9%**, pico de 37.6%
  - customers-service (Cenário B - 80 u): média de **76.4%**, pico de 82.5%
  - customers-service (Cenário C - 150 u): média de **105.0%**, pico de 113.4%
  - vets-service (Cenário A - 30 u): média de **12.0%**, pico de 13.0%
  - vets-service (Cenário B - 80 u): média de **23.7%**, pico de 25.6%
  - vets-service (Cenário C - 150 u): média de **35.1%**, pico de 37.7%
  - visits-service (Cenário A - 30 u): média de **6.5%**, pico de 7.0%
  - visits-service (Cenário B - 80 u): média de **10.4%**, pico de 11.2%
  - visits-service (Cenário C - 150 u): média de **14.0%**, pico de 15.1%

*Interpretação:* O consumo de CPU cresce de maneira quase monotônica conforme os usuários simultâneos aumentam de 30 para 80 e 150. O `api-gateway` e o `customers-service` concentram a maior parte do uso de CPU: o gateway pelo roteamento reativo contínuo de 100% do tráfego, e o customers-service pelo processamento de 80% a 85% de todas as requisições geradas pelos perfis.

### 6.5. Qual cenário apresenta maior taxa de falhas?

- Cenário C (150 u) / Perfil 2 (Escrita): **0.37% de falhas**
- Cenário C (150 u) / Perfil 1 (Leitura): **0.04% de falhas**
- Cenário A (30 u) / Perfil 1 (Leitura): **0.00% de falhas**
- Cenário A (30 u) / Perfil 2 (Escrita): **0.00% de falhas**
- Cenário B (80 u) / Perfil 1 (Leitura): **0.00% de falhas**
- Cenário B (80 u) / Perfil 2 (Escrita): **0.00% de falhas**

*Interpretação:* O cenário com maior taxa de falhas foi o **Cenário C (150 u) no Perfil 2 (Escrita)** com 0.37%, decorrente de exaustão de conexões ou estouro de timeout (30s) sob alta concorrência.
