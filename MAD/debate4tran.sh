set -e
set -u

# MAD_PATH=$(realpath `dirname $0`)
MAD_PATH=/public14_data/wzy2023/Multi-Agents-Debate

python $MAD_PATH/code/debate4tran.py \
    -i /public14_data/wzy2023/Multi-Agents-Debate/outputs.txt \
    -o $MAD_PATH/data/SQL/output3 \
    -k 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 \
