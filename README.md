# LegalAI
Legal AI a RAG Project

git clone https://github.com/franco-mfg/LegalAI.git

cd LegaAI

docker compose build

docker compose start

Una volta caricato il sistema si deve far generare il db con il seguente comando

*docker exec -it myDevTest sh vrun.sh createdb.py*

I parametri per generare il db sono modificabili nel file docker-compose.yml

EURLEX_TABLE= test  | validation | training
EURLEX_NUM_REC=100  numero di record da processare

