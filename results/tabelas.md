### 5.1. Resumo Geral Consolidado (Média de 10 Repetições)

| Cenário | Perfil | Repetições | Tempo Médio (ms) | Desvio Padrão (ms) | P95 (ms) | Vazão (req/s) | Total Requisições | Falhas (%) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A (30 u) | Perfil 2 (Escrita) | 10 | 20.97 | 0.50 | 39.60 | 17.87 | 6434.50 | 0.00 |
| A (30 u) | Perfil 1 (Leitura) | 10 | 15.03 | 0.38 | 27.90 | 19.00 | 6838.30 | 0.00 |
| B (80 u) | Perfil 2 (Escrita) | 10 | 55.28 | 1.42 | 132.20 | 43.65 | 15714.60 | 0.00 |
| B (80 u) | Perfil 1 (Leitura) | 10 | 41.11 | 0.85 | 98.20 | 49.41 | 17786.90 | 0.00 |
| C (150 u) | Perfil 2 (Escrita) | 10 | 193.11 | 5.92 | 607.70 | 65.15 | 23453.30 | 0.37 |
| C (150 u) | Perfil 1 (Leitura) | 10 | 139.92 | 3.93 | 440.20 | 74.73 | 26903.00 | 0.04 |


### 5.2. Desempenho e Distribuição por Operação

| Cenário | Perfil | Operação | Requisições | Tempo Médio (ms) | P95 (ms) | Falhas (%) | Distribuição (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A (30 u) | Perfil 2 (Escrita) | POST /owners | 2574.10 | 28.64 | 52.60 | 0.00 | 40.00 |
| A (30 u) | Perfil 2 (Escrita) | GET /owners | 1286.80 | 21.20 | 38.60 | 0.00 | 20.00 |
| A (30 u) | Perfil 2 (Escrita) | GET /owners/{id} | 1286.80 | 12.93 | 23.40 | 0.00 | 20.00 |
| A (30 u) | Perfil 2 (Escrita) | GET /vets | 1286.80 | 13.45 | 24.30 | 0.00 | 20.00 |
| A (30 u) | Perfil 1 (Leitura) | GET /owners | 3077.60 | 18.09 | 32.80 | 0.00 | 45.00 |
| A (30 u) | Perfil 1 (Leitura) | GET /owners/{id} | 2393.70 | 11.00 | 19.90 | 0.00 | 35.00 |
| A (30 u) | Perfil 1 (Leitura) | GET /vets | 1025.50 | 12.29 | 22.10 | 0.00 | 15.00 |
| A (30 u) | Perfil 1 (Leitura) | POST /owners | 341.50 | 23.87 | 43.60 | 0.00 | 5.00 |
| B (80 u) | Perfil 2 (Escrita) | POST /owners | 6286.20 | 75.36 | 176.60 | 0.00 | 40.00 |
| B (80 u) | Perfil 2 (Escrita) | GET /owners | 3142.80 | 55.40 | 129.70 | 0.00 | 20.00 |
| B (80 u) | Perfil 2 (Escrita) | GET /owners/{id} | 3142.80 | 34.35 | 80.20 | 0.00 | 20.00 |
| B (80 u) | Perfil 2 (Escrita) | GET /vets | 3142.80 | 35.95 | 84.00 | 0.00 | 20.00 |
| B (80 u) | Perfil 1 (Leitura) | GET /owners | 8004.40 | 49.72 | 116.30 | 0.00 | 45.00 |
| B (80 u) | Perfil 1 (Leitura) | GET /owners/{id} | 6225.70 | 30.16 | 70.20 | 0.00 | 35.00 |
| B (80 u) | Perfil 1 (Leitura) | GET /vets | 2667.90 | 33.16 | 77.50 | 0.00 | 15.00 |
| B (80 u) | Perfil 1 (Leitura) | POST /owners | 888.90 | 64.11 | 150.10 | 0.00 | 5.00 |
| C (150 u) | Perfil 2 (Escrita) | POST /owners | 9381.50 | 277.70 | 860.30 | 0.50 | 40.00 |
| C (150 u) | Perfil 2 (Escrita) | GET /owners | 4690.60 | 205.14 | 635.50 | 0.28 | 20.00 |
| C (150 u) | Perfil 2 (Escrita) | GET /owners/{id} | 4690.60 | 100.09 | 309.80 | 0.28 | 20.00 |
| C (150 u) | Perfil 2 (Escrita) | GET /vets | 4690.60 | 104.91 | 324.90 | 0.28 | 20.00 |
| C (150 u) | Perfil 1 (Leitura) | GET /owners | 12106.80 | 183.22 | 567.60 | 0.04 | 45.00 |
| C (150 u) | Perfil 1 (Leitura) | GET /owners/{id} | 9416.30 | 87.88 | 272.00 | 0.04 | 35.00 |
| C (150 u) | Perfil 1 (Leitura) | GET /vets | 4035.30 | 98.45 | 304.60 | 0.03 | 15.00 |
| C (150 u) | Perfil 1 (Leitura) | POST /owners | 1344.60 | 239.03 | 740.50 | 0.00 | 5.00 |


### 5.3. Utilização de CPU e Memória por Serviço (docker stats)

| Cenário | Perfil | Serviço | CPU Média (%) | CPU Pico (%) | Memória Média (MB) |
| --- | --- | --- | --- | --- | --- |
| A (30 u) | Perfil 2 (Escrita) | api-gateway | 24.03 | 25.98 | 342.63 |
| A (30 u) | Perfil 2 (Escrita) | customers-service | 34.87 | 37.58 | 397.81 |
| A (30 u) | Perfil 2 (Escrita) | vets-service | 12.04 | 12.97 | 312.06 |
| A (30 u) | Perfil 2 (Escrita) | visits-service | 6.53 | 7.03 | 292.81 |
| A (30 u) | Perfil 1 (Leitura) | api-gateway | 23.66 | 25.59 | 342.35 |
| A (30 u) | Perfil 1 (Leitura) | customers-service | 30.75 | 33.10 | 397.46 |
| A (30 u) | Perfil 1 (Leitura) | vets-service | 11.88 | 12.81 | 312.42 |
| A (30 u) | Perfil 1 (Leitura) | visits-service | 6.45 | 6.94 | 292.04 |
| B (80 u) | Perfil 2 (Escrita) | api-gateway | 57.66 | 61.91 | 367.48 |
| B (80 u) | Perfil 2 (Escrita) | customers-service | 76.35 | 82.51 | 422.28 |
| B (80 u) | Perfil 2 (Escrita) | vets-service | 23.71 | 25.62 | 327.67 |
| B (80 u) | Perfil 2 (Escrita) | visits-service | 10.38 | 11.20 | 297.64 |
| B (80 u) | Perfil 1 (Leitura) | api-gateway | 57.96 | 62.42 | 367.60 |
| B (80 u) | Perfil 1 (Leitura) | customers-service | 68.78 | 74.19 | 422.28 |
| B (80 u) | Perfil 1 (Leitura) | vets-service | 23.87 | 25.81 | 327.60 |
| B (80 u) | Perfil 1 (Leitura) | visits-service | 10.50 | 11.30 | 297.40 |
| C (150 u) | Perfil 2 (Escrita) | api-gateway | 85.72 | 92.61 | 397.52 |
| C (150 u) | Perfil 2 (Escrita) | customers-service | 105.04 | 113.39 | 457.69 |
| C (150 u) | Perfil 2 (Escrita) | vets-service | 35.07 | 37.69 | 342.51 |
| C (150 u) | Perfil 2 (Escrita) | visits-service | 14.01 | 15.07 | 308.16 |
| C (150 u) | Perfil 1 (Leitura) | api-gateway | 87.25 | 93.94 | 397.35 |
| C (150 u) | Perfil 1 (Leitura) | customers-service | 95.16 | 102.63 | 457.66 |
| C (150 u) | Perfil 1 (Leitura) | vets-service | 35.51 | 38.22 | 342.70 |
| C (150 u) | Perfil 1 (Leitura) | visits-service | 14.18 | 15.28 | 307.23 |