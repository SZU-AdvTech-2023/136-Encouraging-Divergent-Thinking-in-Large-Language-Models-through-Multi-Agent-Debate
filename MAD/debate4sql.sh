set -e
set -u

# MAD_PATH=$(realpath `dirname $0`)
MAD_PATH=/public24_data/wzy2023/Multi-Agents-Debate

python3 $MAD_PATH/code/debate4sql.py \
    -i /public24_data/wzy2023/Multi-Agents-Debate/output.txt \
    -o $MAD_PATH/data/CommonMT/output \
    -k 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 \
 