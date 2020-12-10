cd biobert
pip install -r requirements.txt
./download.sh
export BIOBERT_DIR=./biobert_v1.1_pubmed
echo $BIOBERT_DIR
# Disease NER
export NER_DIR=../CDR_Data/BC5CDR-disease/
export OUTPUT_DIR=./results_biobert/disease/
mkdir -p $OUTPUT_DIR
python run_ner.py --do_train=true --do_eval=true --vocab_file=$BIOBERT_DIR/vocab.txt --bert_config_file=$BIOBERT_DIR/bert_config.json --init_checkpoint=$BIOBERT_DIR/model.ckpt-1000000 --num_train_epochs=10.0 --data_dir=$NER_DIR --output_dir=$OUTPUT_DIR
# Chemical NER
export NER_DIR=../CDR_Data/BC5CDR-chem/
export OUTPUT_DIR=./results_biobert/chemical/
mkdir -p $OUTPUT_DIR
python run_ner.py --do_train=true --do_eval=true --vocab_file=$BIOBERT_DIR/vocab.txt --bert_config_file=$BIOBERT_DIR/bert_config.json --init_checkpoint=$BIOBERT_DIR/model.ckpt-1000000 --num_train_epochs=10.0 --data_dir=$NER_DIR --output_dir=$OUTPUT_DIR
